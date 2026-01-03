from __future__ import annotations

from typing import Any, Dict, List

from duckduckgo_search import DDGS

from ..config import Settings
from .web_tools import _ddg_html_search


def news_search(settings: Settings, query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": item.get("title"),
                        "href": item.get("href"),
                        "body": item.get("body"),
                    }
                )
        if results:
            return results
    except Exception:
        pass
    return _ddg_html_search(settings=settings, query=query, max_results=max_results)
