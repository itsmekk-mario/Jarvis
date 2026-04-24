from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "jarvis.db"


@dataclass
class ScheduleItem:
    id: int
    title: str
    due_at: str
    note: str


class ScheduleMemory:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    due_at TEXT NOT NULL DEFAULT '',
                    note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def add_schedule(self, title: str, due_at: str = "", note: str = "") -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO schedules (title, due_at, note) VALUES (?, ?, ?)",
                (title.strip(), due_at.strip(), note.strip()),
            )
            return int(cursor.lastrowid)

    def list_schedules(self, limit: int = 20) -> list[ScheduleItem]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, title, due_at, note
                FROM schedules
                ORDER BY
                    CASE WHEN due_at = '' THEN 1 ELSE 0 END,
                    due_at ASC,
                    id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [ScheduleItem(id=row[0], title=row[1], due_at=row[2], note=row[3]) for row in rows]
