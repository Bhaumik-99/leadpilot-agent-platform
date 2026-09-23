import json
import sqlite3
from pathlib import Path
from typing import Any

from app.models.domain import Lead, Message


class Repository:
    def __init__(self, database_path: str):
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id TEXT,
                    event TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def save_lead(self, lead: Lead) -> Lead:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO leads(id, payload) VALUES (?, ?)",
                (lead.id, lead.model_dump_json()),
            )
        return lead

    def get_lead(self, lead_id: str) -> Lead | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return Lead.model_validate_json(row["payload"]) if row else None

    def add_message(self, message: Message) -> Message:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO messages(lead_id, payload, created_at) VALUES (?, ?, ?)",
                (message.lead_id, message.model_dump_json(), message.created_at.isoformat()),
            )
        return message

    def history(self, lead_id: str, limit: int = 30) -> list[Message]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM messages WHERE lead_id = ? ORDER BY id DESC LIMIT ?",
                (lead_id, limit),
            ).fetchall()
        return [Message.model_validate_json(r["payload"]) for r in reversed(rows)]

    def audit(self, lead_id: str | None, event: str, payload: dict[str, Any]) -> None:
        from datetime import datetime, timezone

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO audit_log(lead_id, event, payload, created_at) VALUES (?, ?, ?, ?)",
                (
                    lead_id,
                    event,
                    json.dumps(payload, default=str),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
