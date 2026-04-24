from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from browser_actions import open_instagram, open_url, open_youtube_search
from google_services import (
    create_gmail_draft,
    list_youtube_subscriptions,
    search_gmail,
    search_youtube,
    send_gmail,
)
from search import format_search_results, search_web


SYSTEM_PROMPT = """
너는 개인 AI 비서 Jarvis다.
사용자의 한국어 음성 명령을 이해하고 짧고 자연스럽게 답한다.
최신 정보, 뉴스, 가격, 날씨, 일정, 웹상의 사실 확인이 필요한 질문은 반드시 search_web 함수를 호출한다.
Gmail, YouTube, Instagram, 웹사이트 열기 같은 계정/브라우저 작업은 제공된 함수를 사용한다.
메일은 사용자가 명확히 전송을 요청하지 않으면 초안으로 만든다.
Instagram은 로그인 우회, 비공개 정보 수집, 자동 좋아요/팔로우/DM 발송을 하지 않는다.
검색 결과를 사용할 때는 핵심만 요약하고, 불확실한 내용은 불확실하다고 말한다.
답변은 음성으로 읽기 좋게 3~6문장 안에서 작성한다.
"""


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "최신 정보나 웹 검색이 필요한 질문에 대해 인터넷 검색을 수행한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 자연어 질의",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "검색 결과 개수",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_gmail",
            "description": "사용자의 Gmail에서 메일을 검색하거나 최근 메일을 확인한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gmail 검색 쿼리. 예: newer_than:7d, is:unread, from:example@example.com",
                        "default": "newer_than:7d",
                    },
                    "max_results": {"type": "integer", "default": 5},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_gmail_draft",
            "description": "Gmail 메일 초안을 만든다. 수신자, 제목, 본문이 필요하다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_gmail",
            "description": "Gmail로 메일을 실제 전송한다. 명시적인 전송 요청이 있을 때만 사용한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_youtube_subscriptions",
            "description": "사용자의 YouTube 구독 채널 목록을 가져온다.",
            "parameters": {
                "type": "object",
                "properties": {"max_results": {"type": "integer", "default": 10}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_youtube",
            "description": "YouTube에서 영상을 검색한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_youtube_search",
            "description": "브라우저에서 YouTube 검색 결과 페이지를 연다.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_instagram",
            "description": "브라우저에서 Instagram 홈 또는 공개 프로필을 연다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "열고 싶은 Instagram 사용자명. 없으면 홈을 연다.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "브라우저에서 지정한 URL을 연다.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
]


def _run_tool(name: str, args: dict[str, Any], fallback_query: str) -> str:
    if name == "search_web":
        results = search_web(
            query=args.get("query", fallback_query),
            max_results=int(args.get("max_results", 5)),
        )
        return format_search_results(results)
    if name == "search_gmail":
        return search_gmail(
            query=args.get("query", "newer_than:7d"),
            max_results=int(args.get("max_results", 5)),
        )
    if name == "create_gmail_draft":
        return create_gmail_draft(
            to=args["to"],
            subject=args["subject"],
            body=args["body"],
        )
    if name == "send_gmail":
        return send_gmail(
            to=args["to"],
            subject=args["subject"],
            body=args["body"],
        )
    if name == "list_youtube_subscriptions":
        return list_youtube_subscriptions(max_results=int(args.get("max_results", 10)))
    if name == "search_youtube":
        return search_youtube(
            query=args["query"],
            max_results=int(args.get("max_results", 5)),
        )
    if name == "open_youtube_search":
        return open_youtube_search(query=args["query"])
    if name == "open_instagram":
        return open_instagram(target=args.get("target"))
    if name == "open_url":
        return open_url(url=args["url"])
    return f"지원하지 않는 도구입니다: {name}"


class JarvisBrain:
    def __init__(self) -> None:
        self.client: OpenAI | None = None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _client(self) -> OpenAI:
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
            self.client = OpenAI(api_key=api_key)
        return self.client

    def ask(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})

        client = self._client()
        first = client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        assistant_message = first.choices[0].message
        self.messages.append(assistant_message.model_dump(exclude_none=True))

        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                    tool_content = _run_tool(
                        name=tool_call.function.name,
                        args=args,
                        fallback_query=user_text,
                    )
                except Exception as exc:
                    tool_content = f"도구 실행 중 오류가 발생했습니다: {exc}"

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_content,
                    }
                )

            second = client.chat.completions.create(
                model=self.model,
                messages=self.messages,
            )
            answer = second.choices[0].message.content or "답변을 생성하지 못했습니다."
            self.messages.append({"role": "assistant", "content": answer})
            return answer

        return assistant_message.content or "답변을 생성하지 못했습니다."
