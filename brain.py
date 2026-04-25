from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


VALID_INTENTS = {
    "search",
    "weather",
    "file_search",
    "browse_url",
    "schedule",
    "reply",
    "summarize",
    "open_app",
    "quick_reply",
    "unknown",
}


def load_env_file(path: Path | None = None) -> None:
    env_path = path or Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


load_env_file()


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class IntentResult:
    intent: str
    content: str


class OllamaError(RuntimeError):
    pass


class JarvisBrain:
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.model = model or os.getenv("OLLAMA_MODEL", "gemma3:12b")
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.timeout = timeout or env_int("OLLAMA_TIMEOUT", 240)

    def analyze_intent(self, user_text: str) -> IntentResult:
        fast_intent = self._fast_intent(user_text)
        if fast_intent:
            return fast_intent

        prompt = f"""
너는 로컬 개인 AI 비서 Jarvis의 의도 분석기다.
사용자 입력을 아래 JSON 형식 하나로만 분류해라.
마크다운, 설명, 코드블록, 추가 문장을 절대 출력하지 마라.

허용 intent:
- search: 웹 검색, 최신 정보, 나무위키/유튜브/인터넷 자료 조사
- weather: 현재 날씨, 오늘/내일 날씨, 기온, 비/눈 여부
- file_search: 내 컴퓨터, 저장공간, 파일, 폴더, 문서 찾기
- browse_url: URL을 직접 열어 웹페이지 내용 읽기
- schedule: 일정 추가, 일정 조회, 할 일 관리
- reply: 메시지/카톡/메일 답장 문장 작성
- summarize: 긴 글, 문서, 검색 결과 요약
- open_app: 데스크톱 앱 실행
- unknown: 위에 해당하지 않음

반드시 이 형식만 출력:
{{"intent":"search | weather | file_search | browse_url | schedule | reply | summarize | open_app | unknown","content":"사용자 요청 내용"}}

사용자 입력:
{user_text}
"""
        raw = self._chat(
            [
                {"role": "system", "content": "너는 JSON만 출력하는 의도 분석기다."},
                {"role": "user", "content": prompt},
            ],
            json_mode=True,
        )
        parsed = self._parse_intent_json(raw, user_text)
        return parsed

    def generate(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        else:
            messages.append(
                {
                    "role": "system",
                    "content": "너는 한국어로 간결하고 자연스럽게 답하는 개인 AI 비서 Jarvis다.",
                }
            )
        messages.append({"role": "user", "content": prompt})
        return self._chat(messages, json_mode=False).strip()

    def summarize(self, text: str) -> str:
        return self.generate(
            "다음 내용을 한국어로 핵심만 요약해줘. 중요한 사실, 날짜, 이름, 링크가 있으면 유지해줘.\n\n"
            f"{text}",
            system="너는 한국어 요약 전문가다. 짧고 정확하게 요약한다.",
        )

    def _chat(self, messages: list[dict[str, str]], json_mode: bool) -> str:
        num_predict = 160 if json_mode else env_int("OLLAMA_NUM_PREDICT", 768)
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "temperature": 0.2,
                "num_ctx": env_int("OLLAMA_NUM_CTX", 2048),
                "num_predict": num_predict,
            },
        }
        if env_bool("OLLAMA_THINK"):
            payload["think"] = True
        if json_mode:
            payload["format"] = "json"

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.ConnectionError as exc:
            raise OllamaError(
                "Ollama 서버에 연결할 수 없습니다. 먼저 `ollama serve`가 실행 중인지 확인하세요."
            ) from exc
        except requests.HTTPError as exc:
            detail = response.text.strip()
            if len(detail) > 500:
                detail = f"{detail[:500]}..."
            message = f"Ollama API 오류: {exc}"
            if detail:
                message = f"{message}\n응답 내용: {detail}"
            raise OllamaError(message) from exc
        except requests.RequestException as exc:
            raise OllamaError(f"Ollama 요청 실패: {exc}") from exc

        data = response.json()
        message = data.get("message", {})
        content = strip_thinking(str(message.get("content", "")))
        if not content:
            raise OllamaError("Ollama가 빈 응답을 반환했습니다.")
        return content

    def _parse_intent_json(self, raw: str, fallback_text: str) -> IntentResult:
        data: dict[str, Any] | None = None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except json.JSONDecodeError:
                    data = None

        if not isinstance(data, dict):
            return self._fallback_intent(fallback_text)

        intent = str(data.get("intent", "unknown")).strip()
        content = str(data.get("content", fallback_text)).strip() or fallback_text
        if intent not in VALID_INTENTS:
            intent = "unknown"
        return IntentResult(intent=intent, content=content)

    def _fast_intent(self, text: str) -> IntentResult | None:
        compact = text.replace(" ", "")
        lowered = text.lower().strip()

        if any(word in text for word in ["날씨", "기온", "비 와", "비와", "눈 와", "눈와"]):
            return IntentResult("weather", text)
        if re.search(r"https?://\S+", text):
            return IntentResult("browse_url", text)
        if any(word in text for word in ["내 컴퓨터", "저장공간", "파일", "폴더", "문서"]) and any(
            word in text for word in ["찾아", "검색", "어디", "뒤져", "뒤져봐", "찾아줘"]
        ):
            return IntentResult("file_search", text)
        if any(word in text for word in ["검색", "찾아", "최신", "나무위키", "유튜브", "웹서핑"]):
            return IntentResult("search", text)
        if any(word in text for word in ["일정", "약속", "스케줄", "할 일", "할일"]):
            return IntentResult("schedule", text)
        if any(word in text for word in ["답장", "회신", "메일 써", "카톡"]):
            return IntentResult("reply", text)
        if any(word in text for word in ["요약", "정리해", "줄여줘"]):
            return IntentResult("summarize", text)
        if any(word in text for word in ["열어줘", "실행해", "켜줘", "open"]):
            return IntentResult("open_app", text)
        if compact in {"안녕", "안녕하세요", "하이", "자비스", "고마워", "감사", "땡큐"}:
            return IntentResult("quick_reply", text)
        if lowered in {"hi", "hello", "thanks", "thank you"}:
            return IntentResult("quick_reply", text)

        return None

    def _fallback_intent(self, text: str) -> IntentResult:
        compact = text.replace(" ", "")
        lowered = text.lower()
        if any(word in text for word in ["날씨", "기온", "비 와", "비와", "눈 와", "눈와"]):
            return IntentResult("weather", text)
        if re.search(r"https?://\S+", text):
            return IntentResult("browse_url", text)
        if any(word in text for word in ["내 컴퓨터", "저장공간", "파일", "폴더", "문서"]) and any(
            word in text for word in ["찾아", "검색", "어디", "뒤져", "뒤져봐", "찾아줘"]
        ):
            return IntentResult("file_search", text)
        if any(word in text for word in ["검색", "찾아", "알려줘", "최신", "나무위키", "유튜브", "웹서핑"]):
            return IntentResult("search", text)
        if any(word in text for word in ["일정", "약속", "스케줄", "할 일", "할일"]):
            return IntentResult("schedule", text)
        if any(word in text for word in ["답장", "返信", "메일 문장", "카톡"]):
            return IntentResult("reply", text)
        if any(word in text for word in ["요약", "정리"]) or len(text) > 500:
            return IntentResult("summarize", text)
        if any(word in compact for word in ["열어줘", "실행해", "켜줘"]) or "open " in lowered:
            return IntentResult("open_app", text)
        return IntentResult("unknown", text)


def strip_thinking(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()
