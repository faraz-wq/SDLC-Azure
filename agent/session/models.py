"""Session and project data models."""

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from agent.core.schemas import HumanRequest


class SessionStatus(StrEnum):
    """Lifecycle status of a ticket session."""

    PENDING = "pending"
    RUNNING = "running"
    WAITING_ON_HUMAN = "waiting_on_human"
    DONE = "done"
    FAILED = "failed"
    ABORTED = "aborted"


class TicketRunRecord(BaseModel):
    """Persistent tracking record for a ticket in flight."""

    ticket_id: int
    title: str
    branch_name: str
    worktree_path: str
    status: SessionStatus = SessionStatus.PENDING
    stage: str = "ingest"
    pr_id: int | None = None
    pr_url: str | None = None
    pending_request: HumanRequest | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProjectContext(BaseModel):
    """Context holding paths for the local project workspace."""

    repo_root: Path
    dot_agent_dir: Path
    db_path: Path
    worktrees_dir: Path
    logs_dir: Path
