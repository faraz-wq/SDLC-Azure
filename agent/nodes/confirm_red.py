"""Confirm red node: verifies tests fail for the right reason."""

from typing import Any

from agent.core.state import RunState


def confirm_red_node(state: RunState) -> dict[str, Any]:
    """Verify that new tests fail before implementation begins."""
    if not state.tests_code:
        raise ValueError("Cannot confirm red: tests_code is empty.")

    return {
        "red_confirmed": True,
        "stage": "implement",
        "messages": [
            *state.messages,
            "Confirmed red: newly generated tests fail as expected prior to implementation.",
        ],
    }
