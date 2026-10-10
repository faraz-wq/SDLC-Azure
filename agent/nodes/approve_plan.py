"""Approve plan interrupt node."""

from typing import Any

from agent.core.protocols import HumanChannel
from agent.core.schemas import HumanRequest
from agent.core.state import RunState


def approve_plan_node(state: RunState, channel: HumanChannel) -> dict[str, Any]:
    """Queue plan approval request for human decision and pause run."""
    if not state.plan:
        raise ValueError("Cannot request approval: plan is not set.")

    session_id = f"ado-{state.ticket_id}"
    prompt = (
        f"Proposed Implementation Plan for Ticket #{state.ticket_id}:\n"
        f"Summary: {state.plan.summary}\n"
        f"Chosen Option: {state.plan.chosen_option.id} - {state.plan.chosen_option.description}\n"
        f"Blast Radius Score: {state.plan.blast.score:.1f}\n"
        f"Allowed Files: {state.plan.allowed_files}\n"
        f"Max Diff Lines: {state.plan.max_diff_lines}"
    )

    request = HumanRequest(
        session_id=session_id,
        request_type="plan_approval",
        prompt=prompt,
        options=["Approve", "Reject", "Change Option"],
        metadata={"plan_summary": state.plan.summary},
    )

    channel.ask(session_id, request)

    return {
        "status": "waiting_on_human",
        "stage": "plan_approval",
        "messages": [
            *state.messages,
            f"Queued plan approval request in session {session_id}.",
        ],
    }
