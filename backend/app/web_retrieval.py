"""Small, opt-in web retrieval for chat grounding.

DuckDuckGo is used only to discover public result URLs. Unstructured extracts page
content when installed; BeautifulSoup is the lightweight fallback. Polars normalizes
the bounded result set and removes duplicate URLs when available.
"""
import asyncio
import logging
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup

from .embeddings import rerank, reranker_enabled

log = logging.getLogger("rag.web")
SEARCH_URL = "https://html.duckduckgo.com/html/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AskMyData/1.0)"}
MAX_PAGES = 4
MAX_PAGE_BYTES = 1_500_000


def _result_url(href: str) -> str | None:
    parsed = urlparse(href)
    if parsed.hostname and parsed.hostname.endswith("duckduckgo.com"):
        href = parse_qs(parsed.query).get("uddg", [""])[0]
    p = urlparse(href)
    if p.scheme not in ("http", "https") or not p.hostname:
        return None
    if p.hostname.lower() in {"localhost", "127.0.0.1", "::1"}:
        return None
    return href


def _elements_text(html: str) -> str:
    try:
        from unstructured.partition.html import partition_html
        parts = partition_html(text=html)
        text = "\n".join(str(x).strip() for x in parts if str(x).strip())
        if text:
            return text
    except ImportError:
        pass
    except Exception:
        log.debug("Unstructured HTML extraction failed; using BeautifulSoup", exc_info=True)
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(("script", "style", "noscript", "svg", "nav", "footer", "header")):
        tag.decompose()
    return soup.get_text(" ", strip=True)


def _normalize(rows: list[dict]) -> list[dict]:
    try:
        import polars as pl
        frame = pl.DataFrame(rows).unique(subset=["url"], keep="first", maintain_order=True)
        rows = frame.to_dicts()
    except ImportError:
        seen, unique = set(), []
        for row in rows:
            if row["url"] not in seen:
                seen.add(row["url"])
                unique.append(row)
        rows = unique
    except Exception:
        log.debug("Polars result normalization failed; using Python fallback", exc_info=True)
    return rows[:MAX_PAGES]


async def search(question: str) -> list[dict]:
    """Search and fetch a small number of public pages. Never raises into chat."""
    timeout = httpx.Timeout(12.0, connect=5.0)
    limits = httpx.Limits(max_connections=6, max_keepalive_connections=3)
    try:
        async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True,
                                    headers=HEADERS) as client:
            response = await client.get(SEARCH_URL, params={"q": question})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            candidates = []
            for item in soup.select(".result"):
                a = item.select_one("a.result__a")
                if not a:
                    continue
                url = _result_url(a.get("href", ""))
                if url:
                    snippet = item.select_one(".result__snippet")
                    candidates.append({"title": a.get_text(" ", strip=True)[:300], "url": url,
                                       "snippet": snippet.get_text(" ", strip=True) if snippet else ""})
            candidates = _normalize(candidates)

            async def fetch(row):
                try:
                    r = await client.get(row["url"], headers={"Accept": "text/html"})
                    r.raise_for_status()
                    ctype = r.headers.get("content-type", "").lower()
                    if "html" not in ctype:
                        return None
                    html = r.content[:MAX_PAGE_BYTES].decode(r.encoding or "utf-8", errors="replace")
                    text = await asyncio.to_thread(_elements_text, html)
                    text = " ".join(text.split())[:5000]
                    if not text:
                        text = row["snippet"]
                    return {**row, "text": text[:3500]}
                except Exception as exc:
                    log.debug("Could not fetch web result %s: %s", row["url"], exc)
                    return {**row, "text": row["snippet"]} if row["snippet"] else None

            results = [r for r in await asyncio.gather(*(fetch(row) for row in candidates)) if r and r.get("text")]
            if results and reranker_enabled():
                try:
                    scores = await rerank(question, [f"{r['title']}\n{r['text']}" for r in results])
                    if len(scores) == len(results):
                        for row, score in zip(results, scores):
                            row["rerank_score"] = score
                        results.sort(key=lambda r: r["rerank_score"], reverse=True)
                except Exception:
                    log.exception("FlashRank web re-ranking failed; keeping search-engine order")
            return results
    except Exception as exc:
        log.info("Web search unavailable: %s", exc)
        return []
