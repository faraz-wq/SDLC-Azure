"""Normalized cross-boundary schemas.

All data crossing graph node and module boundaries uses these typed Pydantic models.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class FailureKind(StrEnum):
    """Classification of test / build failure."""

    ASSERTION = "assertion"
    COMPILE = "compile"
    MISSING_IMPORT = "missing_import"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class Comment(BaseModel):
    """Work item comment."""

    id: str
    author: str
    body: str
    created_at: datetime | None = None


class Ticket(BaseModel):
    """Normalized ticket ingested from ADO."""

    id: int
    title: str
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    comments: list[Comment] = Field(default_factory=list)
    linked_items: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class Option(BaseModel):
    """Proposed implementation option."""

    id: str
    description: str
    files_touched: list[str] = Field(default_factory=list)
    expected_api_changes: list[str] = Field(default_factory=list)


class BlastRadius(BaseModel):
    """Scored blast radius for a proposed option."""

    files_count: int
    api_changes_count: int
    shared_modules_count: int
    score: float
    components: dict[str, float] = Field(default_factory=dict)


class Plan(BaseModel):
    """Frozen approved implementation plan."""

    ticket_id: int
    summary: str
    chosen_option: Option
    rejected_options: list[Option] = Field(default_factory=list)
    blast: BlastRadius
    allowed_files: list[str]
    max_diff_lines: int
    expected_api_changes: list[str] = Field(default_factory=list)
    test_targets: list[str] = Field(default_factory=list)
    approved_by: str | None = None
    approved_at: datetime | None = None


class PRRef(BaseModel):
    """Reference to an opened draft pull request."""

    pr_id: int
    url: str
    branch: str
    title: str


class StepResult(BaseModel):
    """Result of a command or build/lint step."""

    success: bool
    output: str
    exit_code: int = 0
    duration_seconds: float = 0.0


class TestFailure(BaseModel):
    """Individual test failure details."""

    name: str
    message: str
    trace: str = ""
    kind: FailureKind = FailureKind.UNKNOWN


class TestReport(BaseModel):
    """Normalized test execution report."""

    passed: int
    failed: int
    total: int
    failures: list[TestFailure] = Field(default_factory=list)
    duration_seconds: float = 0.0


class Diagnostic(BaseModel):
    """LSP / compiler diagnostic."""

    file: str
    line: int
    column: int
    message: str
    severity: str = "error"
    code: str | None = None


class AppHandle(BaseModel):
    """Handle to a running local application under test."""

    port: int
    process_id: int
    url: str


class VerifierReport(BaseModel):
    """Playwright / verifier execution report."""

    success: bool
    traces: list[str] = Field(default_factory=list)
    screenshots: list[str] = Field(default_factory=list)
    logs: str = ""


class Limits(BaseModel):
    """Execution bounds for coding iterations."""

    max_iterations: int = 5
    max_diff_lines: int = 300
    timeout_seconds: int = 300


class CodingTask(BaseModel):
    """Task specification passed to the coding agent."""

    task_id: str
    prompt: str
    allowed_files: list[str]
    limits: Limits = Field(default_factory=Limits)


class CodingResult(BaseModel):
    """Outcome of a coding agent execution."""

    iterations: int
    tokens: int
    final_diff: str
    success: bool


class HumanRequest(BaseModel):
    """Interrupt payload requesting human interaction."""

    session_id: str
    request_type: str  # questions, plan_approval, pr_approval
    prompt: str
    options: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HumanResponse(BaseModel):
    """Human response resuming a session."""

    session_id: str
    decision: str  # answered, approved, rejected
    answers: dict[str, str] = Field(default_factory=dict)
    feedback: str = ""


class RunMetrics(BaseModel):
    """Telemetry record for an SDLC agent run."""

    run_id: str
    ticket_id: int
    clarification_asked: bool = False
    questions_count: int = 0
    iterations_count: int = 0
    wall_time_seconds: float = 0.0
    tokens_used: int = 0
    diff_lines: int = 0
    outcome: str = "pending"
