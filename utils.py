from __future__ import annotations

import json
import re
from typing import Any


def compact_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def safe_json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def print_box(title: str, body: str) -> None:
    line = "=" * max(12, len(title) + 8)
    print(f"\n{line}\n[{title}]\n{body}\n{line}\n")
