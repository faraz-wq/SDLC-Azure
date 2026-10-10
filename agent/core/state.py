"""Agent state definitions."""

from pydantic import BaseModel, Field

from agent.core.schemas import BlastRadius, Option, Plan, PRRef, TestReport, Ticket


class RunState(BaseModel):
    """Core state for the SDLC agent run."""

    run_id: str
    ticket_id: int = 0
    step_count: int = 0
    messages: list[str] = Field(default_factory=list)
    status: str = "pending"
    stage: str = "ingest"
    branch_name: str = ""
    worktree_path: str = ""

    # Ingestion & Clarification
    ticket: Ticket | None = None
    rubric_score: float = 0.0
    clarification_questions: list[str] = Field(default_factory=list)
    clarification_answers: dict[str, str] = Field(default_factory=dict)

    # Planning & Blast Radius
    options: list[Option] = Field(default_factory=list)
    blast_scores: list[BlastRadius] = Field(default_factory=list)
    plan: Plan | None = None

    # Tests First
    tests_code: dict[str, str] = Field(default_factory=dict)
    red_confirmed: bool = False

    # Implementation & Verification
    iteration: int = 0
    diff: str = ""
    test_report: TestReport | None = None

    # PR & Final
    pr_ref: PRRef | None = None
    error: str | None = None
