"""Local project directory and ticket registry management."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from agent.session.models import ProjectContext, TicketRunRecord


class ProjectManager:
    """Manages .agent/ project structure and SQLite ticket run registry."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or Path.cwd()
        self.dot_agent_dir = self.root_dir / ".agent"
        self.db_path = self.dot_agent_dir / "sessions.sqlite"
        self.worktrees_dir = self.dot_agent_dir / "worktrees"
        self.logs_dir = self.dot_agent_dir / "logs"

    def initialize(self) -> ProjectContext:
        """Create workspace directories and initialize SQLite tables."""
        self.dot_agent_dir.mkdir(parents=True, exist_ok=True)
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ticket_runs (
                    ticket_id INTEGER PRIMARY KEY,
                    data TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

        return ProjectContext(
            repo_root=self.root_dir,
            dot_agent_dir=self.dot_agent_dir,
            db_path=self.db_path,
            worktrees_dir=self.worktrees_dir,
            logs_dir=self.logs_dir,
        )

    def save_ticket_run(self, record: TicketRunRecord) -> None:
        """Persist or update a ticket run record in SQLite."""
        self.initialize()
        record.updated_at = datetime.now(UTC)
        payload = record.model_dump_json()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO ticket_runs (ticket_id, data, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(ticket_id) DO UPDATE SET
                    data=excluded.data,
                    updated_at=excluded.updated_at
                """,
                (record.ticket_id, payload, record.updated_at.isoformat()),
            )
            conn.commit()

    def get_ticket_run(self, ticket_id: int) -> TicketRunRecord | None:
        """Retrieve a ticket run record by ticket id."""
        if not self.db_path.exists():
            return None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM ticket_runs WHERE ticket_id = ?", (ticket_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return TicketRunRecord.model_validate(json.loads(row[0]))

    def list_ticket_runs(self) -> list[TicketRunRecord]:
        """List all tracked ticket runs sorted by most recent activity."""
        if not self.db_path.exists():
            return []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM ticket_runs ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            return [TicketRunRecord.model_validate(json.loads(r[0])) for r in rows]

    def delete_ticket_run(self, ticket_id: int) -> None:
        """Delete a ticket run record from SQLite."""
        if not self.db_path.exists():
            return

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM ticket_runs WHERE ticket_id = ?", (ticket_id,))
            conn.commit()
