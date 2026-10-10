"""Approve PR node: human approval interrupt before opening PR."""

from typing import Any

from agent.core.protocols import HumanChannel
from agent.core.schemas import HumanRequest
from agent.core.state import RunState


def approve_pr_node(state: RunState, channel: HumanChannel) -> dict[str, Any]:
    """Queue human PR approval request and pause graph before opening draft PR."""
    session_id = f"ado-{state.ticket_id}"
    diff_lines = len(state.diff.splitlines())

    prompt = (
        f"Draft PR Ready for Ticket #{state.ticket_id}:\n"
        f"Branch: {state.branch_name}\n"
        f"Diff Size: {diff_lines} lines\n"
        f"Plan Summary: {state.plan.summary if state.plan else 'N/A'}\n"
        "Do you approve opening a draft pull request in Azure DevOps?"
    )

    request = HumanRequest(
        session_id=session_id,
        request_type="pr_approval",
        prompt=prompt,
        options=["Approve PR", "Reject"],
    )

    channel.ask(session_id, request)

    return {
        "status": "waiting_on_human",
        "stage": "pr_approval",
        "messages": [
            *state.messages,
            f"Queued PR approval request in session {session_id}.",
        ],
    }
