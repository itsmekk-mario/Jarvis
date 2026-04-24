from __future__ import annotations

import os
import re
import subprocess
import urllib.parse
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from brain import JarvisBrain
from memory import ScheduleMemory
from utils import compact_whitespace


@dataclass
class ActionResult:
    title: str
    content: str


class JarvisActions:
    def __init__(self, brain: JarvisBrain, memory: ScheduleMemory | None = None) -> None:
        self.brain = brain
        self.memory = memory or ScheduleMemory()

    def run(self, intent: str, content: str) -> ActionResult:
        if intent == "search":
            return self.search_web(content)
        if intent == "schedule":
            return self.handle_schedule(content)
        if intent == "reply":
            return self.generate_reply(content)
        if intent == "summarize":
            return self.summarize_text(content)
        if intent == "open_app":
            return self.open_app(content)
        return self.unknown(content)

    def search_web(self, query: str) -> ActionResult:
        try:
            results = duckduckgo_search(query)
        except Exception as exc:
            return ActionResult("웹 검색 오류", f"검색 중 오류가 발생했습니다: {exc}")

        if not results:
            return ActionResult("웹 검색", "검색 결과를 찾지 못했습니다.")

        raw = "\n\n".join(
            f"{index}. {item['title']}\n{item['url']}\n{item['snippet']}"
            for index, item in enumerate(results, start=1)
        )
        summary = self.brain.generate(
            f"사용자 질문: {query}\n\n검색 결과:\n{raw}\n\n"
            "위 검색 결과를 바탕으로 한국어로 핵심을 요약해줘. 출처 URL도 2~4개 포함해줘.",
            system="너는 웹 검색 결과를 검토해 정확히 요약하는 리서치 비서다.",
        )
        return ActionResult("웹 검색 요약", summary)

    def handle_schedule(self, text: str) -> ActionResult:
        if any(word in text for word in ["조회", "보여", "목록", "뭐 있", "확인"]):
            items = self.memory.list_schedules()
            if not items:
                return ActionResult("일정 조회", "저장된 일정이 없습니다.")
            lines = []
            for item in items:
                due = f" / {item.due_at}" if item.due_at else ""
                note = f" - {item.note}" if item.note else ""
                lines.append(f"{item.id}. {item.title}{due}{note}")
            return ActionResult("일정 조회", "\n".join(lines))

        title, due_at = parse_schedule_text(text)
        schedule_id = self.memory.add_schedule(title=title, due_at=due_at, note=text)
        due_message = f" 날짜/시간: {due_at}" if due_at else ""
        return ActionResult("일정 추가", f"일정을 추가했습니다. ID: {schedule_id}.{due_message}\n제목: {title}")

    def generate_reply(self, text: str) -> ActionResult:
        reply = self.brain.generate(
            "아래 메시지에 보낼 자연스러운 한국어 답장을 작성해줘. "
            "상대방에게 바로 보낼 수 있게 답장 문장만 작성해줘.\n\n"
            f"{text}",
            system="너는 예의 있고 자연스러운 한국어 답장을 작성하는 비서다.",
        )
        return ActionResult("답장 생성", reply)

    def summarize_text(self, text: str) -> ActionResult:
        return ActionResult("요약", self.brain.summarize(text))

    def open_app(self, text: str) -> ActionResult:
        app_name = extract_app_name(text)
        if not app_name:
            return ActionResult("앱 실행", "실행할 앱 이름을 찾지 못했습니다. 예: 사파리 열어줘")

        try:
            subprocess.run(["open", "-a", app_name], check=True)
        except subprocess.CalledProcessError:
            return ActionResult("앱 실행 오류", f"'{app_name}' 앱을 실행하지 못했습니다. 앱 이름을 확인해 주세요.")
        return ActionResult("앱 실행", f"'{app_name}' 앱을 실행했습니다.")

    def unknown(self, text: str) -> ActionResult:
        answer = self.brain.generate(
            f"사용자 요청을 처리할 수 있는 도구가 없을 때의 짧은 한국어 답변을 해줘.\n요청: {text}",
            system="너는 개인 AI 비서 Jarvis다.",
        )
        return ActionResult("일반 응답", answer)


def duckduckgo_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    if "나무위키" in query and "site:namu.wiki" not in query:
        query = f"{query} site:namu.wiki"
    if "유튜브" in query and "site:youtube.com" not in query:
        query = f"{query} site:youtube.com"

    encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for result in soup.select(".result"):
        title_node = result.select_one(".result__title a")
        snippet_node = result.select_one(".result__snippet")
        if not title_node:
            continue
        title = compact_whitespace(title_node.get_text(" "))
        href = title_node.get("href", "")
        snippet = compact_whitespace(snippet_node.get_text(" ")) if snippet_node else ""
        if title and href:
            results.append({"title": title, "url": normalize_duckduckgo_url(href), "snippet": snippet})
        if len(results) >= max_results:
            break
    return results


def normalize_duckduckgo_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return query["uddg"][0]
    return url


def parse_schedule_text(text: str) -> tuple[str, str]:
    cleaned = text
    for token in ["일정", "추가", "등록", "저장", "해줘", "잡아줘"]:
        cleaned = cleaned.replace(token, " ")
    cleaned = compact_whitespace(cleaned)

    due_patterns = [
        r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}(?:\s+\d{1,2}:\d{2})?)",
        r"((?:오늘|내일|모레|다음 주|이번 주)\s*(?:오전|오후)?\s*\d{0,2}시?\s*\d{0,2}분?)",
    ]
    due_at = ""
    for pattern in due_patterns:
        match = re.search(pattern, text)
        if match:
            due_at = compact_whitespace(match.group(1))
            break
    title = cleaned or text
    return title, due_at


def extract_app_name(text: str) -> str:
    aliases = {
        "사파리": "Safari",
        "크롬": "Google Chrome",
        "구글 크롬": "Google Chrome",
        "메모": "Notes",
        "노트": "Notes",
        "캘린더": "Calendar",
        "터미널": "Terminal",
        "카카오톡": "KakaoTalk",
        "카톡": "KakaoTalk",
        "메일": "Mail",
        "음악": "Music",
    }
    for korean, app in aliases.items():
        if korean in text:
            return app

    cleaned = text
    for token in ["열어줘", "실행해", "켜줘", "앱", "open", "실행", "열어"]:
        cleaned = cleaned.replace(token, " ")
    return compact_whitespace(cleaned)
