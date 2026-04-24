from __future__ import annotations

import urllib.parse
import webbrowser


def open_url(url: str) -> str:
    webbrowser.open(url)
    return f"브라우저에서 열었습니다: {url}"


def open_youtube_search(query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    return open_url(f"https://www.youtube.com/results?search_query={encoded}")


def open_instagram(target: str | None = None) -> str:
    if target:
        clean_target = target.strip().lstrip("@")
        return open_url(f"https://www.instagram.com/{clean_target}/")
    return open_url("https://www.instagram.com/")
