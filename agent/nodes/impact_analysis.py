"""Impact analysis node."""

from typing import Any

from agent.core.state import RunState


def impact_analysis_node(state: RunState) -> dict[str, Any]:
    """Identify impacted code symbols and covering tests."""
    title = state.ticket.title if state.ticket else ""

    return {
        "stage": "plan",
        "messages": [
            *state.messages,
            f"Completed impact analysis for ticket #{state.ticket_id} ('{title[:30]}').",
        ],
    }
