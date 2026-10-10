"""Agent state definitions."""

from pydantic import BaseModel, Field


class RunState(BaseModel):
    """Core state for the SDLC agent run."""

    run_id: str
    step_count: int = 0
    messages: list[str] = Field(default_factory=list)
    status: str = "pending"
    clarification_answers: dict[str, str] = Field(default_factory=dict)
