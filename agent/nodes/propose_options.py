"""Propose options node."""

import json
from typing import Any

from pydantic import BaseModel, Field

from agent.core.protocols import LLMClient
from agent.core.schemas import Option
from agent.core.state import RunState


class OptionsOutput(BaseModel):
    """Schema for proposed options from LLM."""

    options: list[Option] = Field(default_factory=list)


def propose_options_node(state: RunState, llm: LLMClient) -> dict[str, Any]:
    """Propose 2-3 implementation options with files touched and API changes."""
    ticket = state.ticket
    title = ticket.title if ticket else "Feature"
    desc = ticket.description if ticket else ""
    criteria = ticket.acceptance_criteria if ticket else []

    prompt = f"""Propose 2-3 implementation options for this work item:

Title: {title}
Description: {desc}
Acceptance Criteria: {criteria}

For each option, provide:
- id: string like "opt-1", "opt-2"
- description: clear summary of approach
- files_touched: list of specific file paths or globs
- expected_api_changes: list of API/schema modifications (empty if internal only)
"""

    options: list[Option] = []
    try:
        res = llm.complete(
            role="plan",
            messages=[{"role": "user", "content": prompt}],
            schema=OptionsOutput,
            session_id=f"ado-{state.ticket_id}",
        )
        if res.parsed and isinstance(res.parsed, OptionsOutput) and res.parsed.options:
            options = res.parsed.options
        elif res.text:
            data = json.loads(res.text)
            if "options" in data:
                options = [Option.model_validate(o) for o in data["options"]]
    except Exception:
        pass

    if not options:
        # Default options if LLM outputs empty
        options = [
            Option(
                id="opt-minimal",
                description=f"Minimal targeted fix for {title}",
                files_touched=["src/**/*.cs", "src/**/*.tsx"],
                expected_api_changes=[],
            ),
            Option(
                id="opt-modular",
                description=f"Refactored modular implementation for {title}",
                files_touched=["src/**/*.cs", "src/**/*.tsx", "src/Shared/**/*"],
                expected_api_changes=[],
            ),
        ]

    return {
        "options": options,
        "messages": [
            *state.messages,
            f"Generated {len(options)} candidate implementation options.",
        ],
    }
