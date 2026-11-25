import unittest
from unittest.mock import AsyncMock, patch

from app.agentic_graph import (
    AgenticGraphState,
    build_agentic_rag_graph,
    grade_retrieval_node,
    route_node,
    run_agentic_chat,
)


class TestAgenticGraph(unittest.IsolatedAsyncioTestCase):
    def test_graph_compiles(self):
        graph = build_agentic_rag_graph()
        self.assertIsNotNone(graph)
        nodes = graph.nodes
        self.assertIn("router", nodes)
        self.assertIn("condense", nodes)
        self.assertIn("retrieve", nodes)
        self.assertIn("grade_retrieval", nodes)
        self.assertIn("rewrite_query", nodes)
        self.assertIn("assemble_context", nodes)

    async def test_route_small_talk(self):
        state: AgenticGraphState = {"question": "hello!", "doc": False, "mode": "ai"}
        out = await route_node(state)
        self.assertEqual(out.get("route"), "small_talk")

    async def test_route_search_only(self):
        state: AgenticGraphState = {"question": "who is the HR lead?", "doc": False, "mode": "search"}
        out = await route_node(state)
        self.assertEqual(out.get("route"), "search_only")

    async def test_route_rag_default(self):
        state: AgenticGraphState = {"question": "tell me about refund policy", "doc": False, "mode": "ai"}
        out = await route_node(state)
        self.assertEqual(out.get("route"), "rag")
        self.assertEqual(out.get("rewrite_count"), 0)

    async def test_grade_retrieval_needs_rewrite(self):
        state: AgenticGraphState = {
            "condensed_question": "pension scheme ke baare mein batao",
            "runtime": {"effective_ai_min_score": 0.6, "query_rewrite": True},
            "exact": False,
            "confidence": 0.3,
            "rewrite_count": 0,
        }
        out = await grade_retrieval_node(state)
        self.assertTrue(out.get("should_rewrite"))

    async def test_grade_retrieval_good_score_no_rewrite(self):
        state: AgenticGraphState = {
            "condensed_question": "pension scheme ke baare mein batao",
            "runtime": {"effective_ai_min_score": 0.6, "query_rewrite": True},
            "exact": False,
            "confidence": 0.85,
            "rewrite_count": 0,
        }
        out = await grade_retrieval_node(state)
        self.assertFalse(out.get("should_rewrite"))

    @patch("app.agentic_graph.get_runtime")
    @patch("app.agentic_graph.llm.chat")
    async def test_run_agentic_chat_small_talk_stream(self, mock_chat, mock_runtime):
        mock_runtime.return_value = {
            "send_context_to_external": True,
            "ai_fallback": True,
            "cache_enabled": False,
        }
        mock_res = AsyncMock()
        mock_res.text = "Hello! How can I help you today?"
        mock_res.provider = "test_llm"
        mock_res.model = "test_model"
        mock_chat.return_value = mock_res

        events = []
        async for ev in run_agentic_chat("hi", [], mode="ai"):
            events.append(ev)

        types = [e["type"] for e in events]
        self.assertIn("meta", types)
        self.assertIn("token", types)
        self.assertIn("done", types)
        meta_ev = next(e for e in events if e["type"] == "meta")
        self.assertEqual(meta_ev.get("graph_path"), "small_talk")


if __name__ == "__main__":
    unittest.main()
