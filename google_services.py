from __future__ import annotations

import base64
import os
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/youtube.readonly",
]


class GoogleServiceError(RuntimeError):
    pass


def _path_from_env(name: str, default: str) -> Path:
    return Path(os.getenv(name, default)).expanduser().resolve()


def get_credentials() -> Credentials:
    client_secret_file = _path_from_env("GOOGLE_CLIENT_SECRET_FILE", "credentials.json")
    token_file = _path_from_env("GOOGLE_TOKEN_FILE", "token.json")

    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not client_secret_file.exists():
            raise GoogleServiceError(
                f"Google OAuth 클라이언트 파일을 찾을 수 없습니다: {client_secret_file}"
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_file), SCOPES)
        creds = flow.run_local_server(port=0)

    token_file.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _gmail_service():
    return build("gmail", "v1", credentials=get_credentials())


def _youtube_service():
    return build("youtube", "v3", credentials=get_credentials())


def _header_value(headers: list[dict[str, str]], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def search_gmail(query: str = "newer_than:7d", max_results: int = 5) -> str:
    service = _gmail_service()
    response = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    messages = response.get("messages", [])
    if not messages:
        return "조건에 맞는 메일이 없습니다."

    summaries = []
    for item in messages:
        message = (
            service.users()
            .messages()
            .get(userId="me", id=item["id"], format="metadata")
            .execute()
        )
        payload: dict[str, Any] = message.get("payload", {})
        headers = payload.get("headers", [])
        summaries.append(
            "\n".join(
                [
                    f"보낸 사람: {_header_value(headers, 'From')}",
                    f"제목: {_header_value(headers, 'Subject')}",
                    f"날짜: {_header_value(headers, 'Date')}",
                    f"미리보기: {message.get('snippet', '')}",
                ]
            )
        )
    return "\n\n".join(summaries)


def create_gmail_draft(to: str, subject: str, body: str) -> str:
    service = _gmail_service()
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    draft = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": encoded_message}})
        .execute()
    )
    return f"메일 초안을 만들었습니다. draft id: {draft.get('id', '')}"


def send_gmail(to: str, subject: str, body: str) -> str:
    if os.getenv("JARVIS_ALLOW_EMAIL_SEND", "false").lower() != "true":
        return "안전을 위해 실제 메일 전송은 비활성화되어 있습니다. 초안 생성 명령을 사용하거나 JARVIS_ALLOW_EMAIL_SEND=true로 설정하세요."

    service = _gmail_service()
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    sent = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": encoded_message})
        .execute()
    )
    return f"메일을 보냈습니다. message id: {sent.get('id', '')}"


def list_youtube_subscriptions(max_results: int = 10) -> str:
    service = _youtube_service()
    response = (
        service.subscriptions()
        .list(part="snippet", mine=True, maxResults=max_results)
        .execute()
    )
    items = response.get("items", [])
    if not items:
        return "구독 중인 채널을 찾지 못했습니다."

    lines = []
    for item in items:
        snippet = item.get("snippet", {})
        lines.append(
            f"채널: {snippet.get('title', '')}\n설명: {snippet.get('description', '')[:160]}"
        )
    return "\n\n".join(lines)


def search_youtube(query: str, max_results: int = 5) -> str:
    service = _youtube_service()
    response = (
        service.search()
        .list(part="snippet", q=query, type="video", maxResults=max_results)
        .execute()
    )
    items = response.get("items", [])
    if not items:
        return "유튜브 검색 결과가 없습니다."

    lines = []
    for item in items:
        video_id = item.get("id", {}).get("videoId", "")
        snippet = item.get("snippet", {})
        lines.append(
            "\n".join(
                [
                    f"제목: {snippet.get('title', '')}",
                    f"채널: {snippet.get('channelTitle', '')}",
                    f"URL: https://www.youtube.com/watch?v={video_id}",
                    f"설명: {snippet.get('description', '')[:180]}",
                ]
            )
        )
    return "\n\n".join(lines)
