"""Rubric loader and scoring helper."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class Criterion(BaseModel):
    """Individual scoring criterion."""

    weight: float
    description: str


class TicketRubric(BaseModel):
    """Rubric configuration."""

    threshold: float = 7.0
    criteria: dict[str, Criterion] = Field(default_factory=dict)


def load_rubric(path: Path | None = None) -> TicketRubric:
    """Load rubric from YAML file."""
    rubric_file = path or (Path(__file__).parent / "ticket_rubric.yaml")
    if not rubric_file.exists():
        return TicketRubric()

    data: dict[str, Any] = yaml.safe_load(rubric_file.read_text()) or {}
    return TicketRubric.model_validate(data)
