from __future__ import annotations

import os
from typing import Any

import requests


class WebSearchError(RuntimeError):
    pass


def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search the web using Tavily and return normalized result items."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise WebSearchError("TAVILY_API_KEY가 설정되어 있지 않습니다.")

    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": False,
        },
        timeout=20,
    )
    response.raise_for_status()
    payload: dict[str, Any] = response.json()

    results = []
    for item in payload.get("results", []):
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            }
        )
    return results


def format_search_results(results: list[dict[str, str]]) -> str:
    if not results:
        return "검색 결과가 없습니다."

    lines = []
    for index, item in enumerate(results, start=1):
        lines.append(
            f"{index}. 제목: {item['title']}\n"
            f"   URL: {item['url']}\n"
            f"   내용: {item['content']}"
        )
    return "\n".join(lines)
