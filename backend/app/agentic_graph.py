"""LangGraph Agentic RAG and Multi-Agent Workflow.

Enhances the project with:
1. A stateful StateGraph workflow with cyclic self-correction (CRAG).
2. Autonomous Intent Routing (Small Talk vs Fast Search vs RAG vs Agent Skills).
3. Retrieval Grading (evaluates retrieved chunks and triggers query rewriting if relevance is low).
4. Dynamic Agent Skill Activation (injects specialized skills matching task profile).
5. Seamless streaming SSE generator compatible with the frontend UI.
"""
from __future__ import annotations

import logging
from typing import Any, AsyncGenerator, TypedDict

from langgraph.graph import END, StateGraph

from . import chat, intelligence, knowledge, llm, offline, skill_hub
from .embeddings import embed_query
from .runtime_settings import get_runtime

log = logging.getLogger("rag.agentic_graph")


class AgenticGraphState(TypedDict, total=False):
    # Inputs & config
    question: str
    original_question: str
    history: list[dict]
    mode: str
    namespaces: list[str] | None
    allow_ai: bool | None
    doc: bool
    doc_style: str | None
    runtime: dict

    # Routing & Condense
    route: str  # "small_talk" | "search_only" | "cache_hit" | "rag" | "fallback_ai"
    condensed_question: str
    query_vector: list[float]
    task_profile: str

    # Retrieval & Self-RAG Grading
    chunks: list[dict]
    confidence: float
    exact: bool
    citations: list[dict]
    rewrite_count: int
    should_rewrite: bool
    cache_hit: dict | None

    # Agent Skills & Context
    hub: Any
    system_prompt: str
    user_prompt: str
    stream_type: str  # "small_talk" | "search" | "grounded" | "fallback"
    answer_tokens: int


# ---------------------------------------------------------------- Nodes
async def route_node(state: AgenticGraphState) -> dict:
    """Analyze the user's intent: small talk, database search only, or RAG."""
    q = state["question"]
    doc = state.get("doc", False)
    mode = state.get("mode", "ai")

    if not doc and offline.small_talk_kind(q):
        return {"route": "small_talk"}

    if mode == "search":
        return {"route": "search_only"}

    return {"route": "rag", "rewrite_count": 0, "should_rewrite": False}


async def condense_node(state: AgenticGraphState) -> dict:
    """Condense multi-turn conversation into a standalone search question."""
    q = state["question"]
    history = state.get("history", [])
    s = state["runtime"]
    trusted_only = not s.get("send_context_to_external", True)

    condensed = await chat._condense(q, history, trusted_only)
    qv = await embed_query(condensed)

    # Check cache if enabled
    cache_hit = None
    if s.get("cache_enabled") and not state.get("doc"):
        ai_ok = s.get("ai_fallback", True) and state.get("allow_ai") is not False
        hit = await knowledge.cache_lookup(condensed, qv, s.get("cache_threshold", 0.9), state.get("namespaces"))
        if hit and (ai_ok or hit.get("source") != "ai"):
            cache_hit = hit

    return {
        "condensed_question": condensed,
        "query_vector": qv,
        "cache_hit": cache_hit,
    }


async def retrieve_node(state: AgenticGraphState) -> dict:
    """Retrieve documents using hybrid vector & exact match search."""
    q = state["condensed_question"]
    qv = state["query_vector"]
    s = state["runtime"]
    namespaces = state.get("namespaces")

    chunks, confidence, exact = await knowledge.retrieve(q, qv, s.get("top_k", 5), namespaces)
    return {
        "chunks": chunks,
        "confidence": confidence,
        "exact": exact,
        "citations": chat._citations(chunks),
    }


async def grade_retrieval_node(state: AgenticGraphState) -> dict:
    """Evaluate retrieved documents against thresholds (Self-RAG grading)."""
    s = state["runtime"]
    loose = s.get("effective_ai_min_score", 0.55)
    exact = state.get("exact", False)
    conf = state.get("confidence", 0.0)
    count = state.get("rewrite_count", 0)
    q = state["condensed_question"]

    # Needs rewrite if score is weak, rewriting enabled, and under retry limit
    if not (exact or conf >= loose) and s.get("query_rewrite") and intelligence.needs_rewrite(q) and count < 1:
        return {"should_rewrite": True}

    return {"should_rewrite": False}


async def rewrite_query_node(state: AgenticGraphState) -> dict:
    """Rewrite Hindi/Hinglish or ambiguous queries into clean search terms."""
    q = state["condensed_question"]
    s = state["runtime"]
    trusted_only = not s.get("send_context_to_external", True)
    count = state.get("rewrite_count", 0) + 1

    rq = await chat._ask(chat.REWRITE_SYSTEM, q, trusted_only, 60)
    if rq and rq.lower() != q.lower() and len(rq) < 500:
        new_qv = await embed_query(rq)
        return {"condensed_question": rq, "query_vector": new_qv, "rewrite_count": count, "should_rewrite": False}

    return {"rewrite_count": count, "should_rewrite": False}


async def assemble_context_node(state: AgenticGraphState) -> dict:
    """Determine whether to ground from data or invoke skill-based fallback."""
    chunks = state.get("chunks", [])
    exact = state.get("exact", False)
    confidence = state.get("confidence", 0.0)
    s = state["runtime"]
    loose = s.get("effective_ai_min_score", 0.55)
    doc = state.get("doc", False)
    style = (state.get("doc_style") or chat.DOC_STYLE) if doc else ""
    q = state["condensed_question"]
    trusted_only = not s.get("send_context_to_external", True)

    # If relevant chunks exist, prepare grounded response
    if chunks and (exact or confidence >= loose):
        return {
            "stream_type": "grounded",
            "system_prompt": chat.GROUNDED_SYSTEM + style,
            "user_prompt": f"CONTEXT:\n{chat._context(chunks, s.get('max_context_chars', 4000))}\n\nQUESTION: {q}",
            "answer_tokens": 2500 if doc else 1200,
        }

    # Otherwise, fallback with Agent Skills attached
    task_profile = intelligence.classify_task(q)
    hub = await skill_hub.build(q, task_profile, chunks, s, trusted_only)
    return {
        "stream_type": "fallback",
        "task_profile": task_profile,
        "hub": hub,
        "system_prompt": chat.FALLBACK_SYSTEM + hub.system_extra + style,
        "user_prompt": q,
        "answer_tokens": 2500 if doc else 1500,
    }


# ---------------------------------------------------------------- Graph Definition
def build_agentic_rag_graph():
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(AgenticGraphState)

    workflow.add_node("router", route_node)
    workflow.add_node("condense", condense_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade_retrieval", grade_retrieval_node)
    workflow.add_node("rewrite_query", rewrite_query_node)
    workflow.add_node("assemble_context", assemble_context_node)

    # Entry point
    workflow.set_entry_point("router")

    # Routing edge
    def _route_decider(state: AgenticGraphState) -> str:
        r = state.get("route")
        if r in ("small_talk", "search_only"):
            return END
        return "condense"

    workflow.add_conditional_edges("router", _route_decider, {END: END, "condense": "condense"})

    # Condense to retrieve (or cache hit)
    def _condense_decider(state: AgenticGraphState) -> str:
        if state.get("cache_hit"):
            return END
        return "retrieve"

    workflow.add_conditional_edges("condense", _condense_decider, {END: END, "retrieve": "retrieve"})

    workflow.add_edge("retrieve", "grade_retrieval")

    # Corrective RAG branching
    def _grade_decider(state: AgenticGraphState) -> str:
        if state.get("should_rewrite"):
            return "rewrite_query"
        return "assemble_context"

    workflow.add_conditional_edges("grade_retrieval", _grade_decider, {
        "rewrite_query": "rewrite_query",
        "assemble_context": "assemble_context",
    })

    # Loop back from rewrite to retrieve!
    workflow.add_edge("rewrite_query", "retrieve")
    workflow.add_edge("assemble_context", END)

    return workflow.compile()


# Compiled Singleton Graph
graph = build_agentic_rag_graph()


# ---------------------------------------------------------------- Runner & Streamer
async def run_agentic_chat(
    question: str,
    history: list[dict],
    mode: str = "ai",
    namespaces: list[str] | None = None,
    allow_ai: bool | None = None,
    doc: bool = False,
    doc_style: str | None = None,
) -> AsyncGenerator[dict, None]:
    """Execute the LangGraph Agentic RAG workflow and yield streaming events.

    Produces events matching the SSE contract:
      - meta: metadata, citations, and model information
      - token: individual text streaming tokens
      - done: completion signal
      - error: error notifications
    """
    s = await get_runtime()
    initial_state: AgenticGraphState = {
        "question": question,
        "original_question": question,
        "history": history,
        "mode": mode,
        "namespaces": namespaces,
        "allow_ai": allow_ai,
        "doc": doc,
        "doc_style": doc_style,
        "runtime": s,
    }

    # Execute graph up to context assembly
    state: AgenticGraphState = await graph.ainvoke(initial_state)
    route = state.get("route")
    q = state.get("condensed_question") or question

    # 1. Small Talk
    if route == "small_talk":
        msgs = [{"role": "system", "content": chat.CHAT_SYSTEM}] + [
            {"role": m["role"], "content": m["content"][:1000]} for m in history[-6:]
        ] + [{"role": "user", "content": question}]
        try:
            res = await llm.chat(msgs, temperature=0.7, max_tokens=120, profile="fast")
            if res.text:
                yield chat._meta("ai", question, 1.0, [], res.provider, res.model, graph_path="small_talk")
                yield {"type": "token", "text": res.text}
                yield {"type": "done"}
                return
        except llm.AllProvidersFailed:
            pass
        yield chat._meta("local", question, 1.0, graph_path="small_talk")
        yield {"type": "token", "text": offline.small_talk(question)}
        yield {"type": "done"}
        return

    # 2. Search Only (mode == "search")
    if route == "search_only":
        async for ev in chat._search_only(question, s, namespaces):
            yield ev
        return

    # 3. Cache Hit
    hit = state.get("cache_hit")
    if hit:
        yield chat._meta(
            "cache", q, 1.0, hit.get("citations", []), hit.get("provider"), hit.get("model"),
            graph_path="cache_hit"
        )
        yield {"type": "token", "text": hit["answer"]}
        yield {"type": "done"}
        return

    # 4. Stream Grounded or Fallback Response
    stream_type = state.get("stream_type")
    chunks = state.get("chunks", [])
    citations = state.get("citations", [])
    conf = state.get("confidence", 0.0)
    qv = state.get("query_vector")
    trusted_only = not s.get("send_context_to_external", True)

    if stream_type == "grounded":
        messages = [
            {"role": "system", "content": state["system_prompt"]},
            {"role": "user", "content": state["user_prompt"]},
        ]
        buf, parts, pmeta = [], [], {}
        decided, not_found, failed = False, False, False
        agen = llm.stream_chat(
            messages,
            require_trusted=trusted_only,
            temperature=0.1,
            max_tokens=state["answer_tokens"],
            profile="grounded",
        )
        try:
            async for ev in agen:
                if ev["type"] == "meta":
                    pmeta = ev
                elif ev["type"] == "token":
                    if decided:
                        parts.append(ev["text"])
                        yield ev
                        continue
                    buf.append(ev["text"])
                    verdict = chat._is_not_found("".join(buf))
                    if verdict is True:
                        not_found = True
                        break
                    if verdict is False:
                        decided = True
                        parts.append("".join(buf))
                        yield chat._meta(
                            "database", q, conf, citations, pmeta.get("provider"), pmeta.get("model"),
                            graph_path="agentic_grounded",
                            rewrites=state.get("rewrite_count", 0),
                        )
                        yield {"type": "token", "text": "".join(buf)}
                elif ev["type"] == "error":
                    failed = True
                    yield ev
        except llm.AllProvidersFailed:
            good = chat._best_matches(chunks, s.get("effective_min_score", 0.7))
            if not good:
                yield chat._meta("none", q, conf, note="no AI available", graph_path="agentic_offline")
                yield {"type": "token", "text": offline.not_found(question)}
                yield {"type": "done"}
                return
            yield chat._meta("database", q, conf, chat._citations(good), note="answered offline (no AI available)")
            yield {"type": "token", "text": offline.answer_from_data(good, q)}
            yield {"type": "done"}
            return
        finally:
            await agen.aclose()

        if not decided and not not_found and buf:
            not_found = bool(chat._is_not_found("".join(buf)))
            if not not_found:
                decided = True
                parts.append("".join(buf))
                yield chat._meta(
                    "database", q, conf, citations, pmeta.get("provider"), pmeta.get("model"),
                    graph_path="agentic_grounded",
                )
                yield {"type": "token", "text": "".join(buf)}

        if decided:
            if parts and not failed and not doc and qv:
                await knowledge.cache_store(
                    q, qv, "".join(parts), "database", citations,
                    pmeta.get("provider"), pmeta.get("model"), namespaces,
                )
            yield {"type": "done"}
            return

    # If grounded found nothing or fallback requested:
    ai_ok = s.get("ai_fallback", True) and state.get("allow_ai") is not False
    if not ai_ok:
        yield chat._meta("none", q, conf, graph_path="not_found")
        yield {"type": "token", "text": offline.not_found(question)}
        yield {"type": "done"}
        return

    # Fallback with Agent Skills
    hub = state.get("hub")
    task_profile = state.get("task_profile") or intelligence.classify_task(q)
    if not hub:
        hub = await skill_hub.build(q, task_profile, chunks, s, trusted_only)

    messages = [
        {"role": "system", "content": state.get("system_prompt") or (chat.FALLBACK_SYSTEM + hub.system_extra)},
        {"role": "user", "content": q},
    ]
    parts, meta = [], {}
    try:
        async for ev in llm.stream_chat(
            messages,
            require_trusted=hub.require_trusted,
            max_tokens=state.get("answer_tokens", 1500),
            profile=task_profile,
        ):
            if ev["type"] == "meta":
                meta = ev
                yield chat._meta(
                    "ai", q, conf, [], ev["provider"], ev["model"],
                    task_profile=task_profile,
                    graph_path="agentic_skills_fallback",
                    **hub.meta(),
                )
            elif ev["type"] == "token":
                parts.append(ev["text"])
                yield ev
            else:
                yield ev
    except llm.AllProvidersFailed as e:
        good = chat._best_matches(chunks, s.get("effective_min_score", 0.7))
        if good:
            yield chat._meta("database", q, conf, chat._citations(good), note="answered offline (no AI available)")
            yield {"type": "token", "text": offline.answer_from_data(good, q)}
            yield {"type": "done"}
            return
        yield chat._meta("none", q, conf, note=f"no AI available: {e}")
        yield {"type": "token", "text": offline.not_found(question)}
        yield {"type": "done"}
        return

    if parts and meta and not doc and qv:
        await knowledge.cache_store(q, qv, "".join(parts), "ai", [], meta["provider"], meta["model"], namespaces)
    yield {"type": "done"}

