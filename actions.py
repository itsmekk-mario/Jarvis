from __future__ import annotations

import os
import re
import subprocess
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

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
        if intent == "quick_reply":
            return self.quick_reply(content)
        if intent == "weather":
            return self.weather(content)
        if intent == "file_search":
            return self.search_files(content)
        if intent == "browse_url":
            return self.browse_url(content)
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

    def quick_reply(self, text: str) -> ActionResult:
        compact = text.replace(" ", "")
        if compact in {"고마워", "감사", "땡큐"} or text.lower().strip() in {"thanks", "thank you"}:
            return ActionResult("일반 응답", "언제든지요.")
        return ActionResult("일반 응답", "네, 듣고 있습니다. 무엇을 도와드릴까요?")

    def weather(self, text: str) -> ActionResult:
        location = extract_weather_location(text) or os.getenv("JARVIS_DEFAULT_LOCATION", "Seoul")
        try:
            weather = fetch_weather(location)
        except Exception as exc:
            return ActionResult("날씨 오류", f"날씨 정보를 가져오지 못했습니다: {exc}")

        return ActionResult("날씨", weather)

    def browse_url(self, text: str) -> ActionResult:
        url = extract_url(text)
        if not url:
            return ActionResult("웹페이지 읽기", "읽을 URL을 찾지 못했습니다.")

        try:
            title, page_text = fetch_page_text(url)
        except Exception as exc:
            return ActionResult("웹페이지 읽기 오류", f"페이지를 가져오지 못했습니다: {exc}")

        if not page_text:
            return ActionResult("웹페이지 읽기", "페이지에서 읽을 수 있는 텍스트를 찾지 못했습니다.")

        summary = self.brain.generate(
            f"URL: {url}\n제목: {title}\n\n본문:\n{page_text[:6000]}\n\n"
            "위 웹페이지의 핵심을 한국어로 짧게 요약해줘.",
            system="너는 웹페이지 내용을 읽고 핵심만 요약하는 비서다.",
        )
        return ActionResult("웹페이지 요약", summary)

    def search_files(self, text: str) -> ActionResult:
        query = extract_file_query(text)
        if not query:
            return ActionResult("파일 검색", "찾을 파일명이나 키워드를 알려주세요.")

        results = find_local_files(query)
        if not results:
            return ActionResult("파일 검색", f"'{query}'와 일치하는 파일을 찾지 못했습니다.")

        lines = [f"검색어: {query}", "찾은 항목:"]
        for index, item in enumerate(results, start=1):
            location = item["path"]
            reason = item["match"]
            lines.append(f"{index}. {location}\n   일치: {reason}")
        return ActionResult("파일 검색", "\n".join(lines))

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


def fetch_weather(location: str) -> str:
    encoded = urllib.parse.quote(location)
    response = requests.get(f"https://wttr.in/{encoded}?format=j1&lang=ko", timeout=15)
    response.raise_for_status()
    response.encoding = "utf-8"
    payload = response.json()

    current = payload["current_condition"][0]
    area = payload.get("nearest_area", [{}])[0]
    area_name = area.get("areaName", [{}])[0].get("value", location)
    country = area.get("country", [{}])[0].get("value", "")
    condition = current.get("lang_ko", current.get("weatherDesc", [{"value": ""}]))[0].get("value", "")
    temp = current.get("temp_C", "?")
    feels_like = current.get("FeelsLikeC", "?")
    humidity = current.get("humidity", "?")
    wind = current.get("windspeedKmph", "?")
    rain = current.get("precipMM", "0")

    today = payload.get("weather", [{}])[0]
    hourly = today.get("hourly", [])
    chance_of_rain = max((int(item.get("chanceofrain", 0)) for item in hourly), default=0)
    high = today.get("maxtempC", "?")
    low = today.get("mintempC", "?")

    place = f"{area_name}, {country}".strip(", ")
    return (
        f"{place} 현재 날씨는 {condition or '확인됨'}입니다.\n"
        f"현재 {temp}도, 체감 {feels_like}도, 오늘 최저 {low}도 / 최고 {high}도입니다.\n"
        f"습도 {humidity}%, 바람 {wind}km/h, 강수량 {rain}mm, 오늘 비 올 확률은 최대 {chance_of_rain}%입니다."
    )


def extract_weather_location(text: str) -> str:
    aliases = {
        "서울": "Seoul",
        "부산": "Busan",
        "인천": "Incheon",
        "대구": "Daegu",
        "대전": "Daejeon",
        "광주": "Gwangju",
        "울산": "Ulsan",
        "제주": "Jeju",
        "뉴욕": "New York",
        "런던": "London",
        "도쿄": "Tokyo",
    }
    for korean, english in aliases.items():
        if korean in text:
            return english

    cleaned = text
    for token in ["오늘", "내일", "현재", "날씨", "기온", "알려줘", "어때", "어떤지", "좀"]:
        cleaned = cleaned.replace(token, " ")
    return compact_whitespace(cleaned)


def extract_url(text: str) -> str:
    match = re.search(r"https?://\S+", text)
    return match.group(0).rstrip(".,)") if match else ""


def fetch_page_text(url: str) -> tuple[str, str]:
    response = requests.get(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            )
        },
        timeout=20,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    title = compact_whitespace(soup.title.get_text(" ")) if soup.title else url
    text = compact_whitespace(soup.get_text(" "))
    return title, text


def extract_file_query(text: str) -> str:
    cleaned = text
    for token in [
        "내 컴퓨터",
        "저장공간",
        "파일",
        "폴더",
        "문서",
        "찾아줘",
        "찾아",
        "검색해줘",
        "검색",
        "어디",
        "뒤져봐",
        "뒤져",
        "에서",
    ]:
        cleaned = cleaned.replace(token, " ")
    return compact_whitespace(cleaned)


def find_local_files(query: str) -> list[dict[str, str]]:
    roots = configured_file_roots()
    query_lower = query.lower()
    max_results = int(os.getenv("JARVIS_FILE_SEARCH_MAX_RESULTS", "12"))
    max_files = int(os.getenv("JARVIS_FILE_SEARCH_MAX_FILES", "8000"))
    results: list[dict[str, str]] = []
    scanned = 0

    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [name for name in dirnames if should_scan_dir(name)]
            for filename in filenames:
                scanned += 1
                if scanned > max_files or len(results) >= max_results:
                    return results

                path = Path(dirpath) / filename
                filename_lower = filename.lower()
                if query_lower in filename_lower:
                    results.append({"path": str(path), "match": "파일명"})
                    continue

                if should_scan_file_content(path) and file_contains(path, query_lower):
                    results.append({"path": str(path), "match": "파일 내용"})
    return results


def configured_file_roots() -> list[Path]:
    configured = os.getenv("JARVIS_FILE_SEARCH_ROOTS", "")
    if configured:
        return [Path(item).expanduser() for item in configured.split(",") if item.strip()]

    home = Path.home()
    return [home]


def should_scan_dir(name: str) -> bool:
    blocked = {
        ".git",
        ".venv",
        "__pycache__",
        "node_modules",
        "Library",
        "Applications",
        "System",
        "Pictures",
        "Movies",
        "Music",
    }
    return not name.startswith(".") and name not in blocked


def should_scan_file_content(path: Path) -> bool:
    if path.name.startswith("."):
        return False
    if path.suffix.lower() not in {".txt", ".md", ".csv", ".json", ".py", ".js", ".html", ".css", ".log"}:
        return False
    try:
        return path.stat().st_size <= 1_000_000
    except OSError:
        return False


def file_contains(path: Path, query_lower: str) -> bool:
    try:
        content = path.read_text(errors="ignore")
    except OSError:
        return False
    return query_lower in content.lower()


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
