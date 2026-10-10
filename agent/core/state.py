"""Agent state definitions."""

from pydantic import BaseModel, Field

from agent.core.schemas import Ticket


class RunState(BaseModel):
    """Core state for the SDLC agent run."""

    run_id: str
    ticket_id: int = 0
    step_count: int = 0
    messages: list[str] = Field(default_factory=list)
    status: str = "pending"
    stage: str = "ingest"
    ticket: Ticket | None = None
    rubric_score: float = 0.0
    clarification_questions: list[str] = Field(default_factory=list)
    clarification_answers: dict[str, str] = Field(default_factory=dict)
