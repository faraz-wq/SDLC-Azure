"""Raise draft PR node."""

from typing import Any

from agent.core.protocols import PRHost
from agent.core.state import RunState


def raise_draft_pr_node(state: RunState, pr_host: PRHost) -> dict[str, Any]:
    """Create draft pull request via PRHost connector with work item linkage."""
    title = f"Draft: {state.ticket.title if state.ticket else f'Ticket #{state.ticket_id}'}"
    plan_desc = state.plan.summary if state.plan else "Implemented solution"
    body = (
        f"### SDLC Agent Automated Draft PR\n\n"
        f"**Work Item:** #{state.ticket_id}\n\n"
        f"**Plan Summary:** {plan_desc}\n\n"
        f"**Branch:** `{state.branch_name}`\n"
    )

    pr_ref = pr_host.create_draft_pr(
        branch=state.branch_name,
        title=title,
        body=body,
        work_item=state.ticket_id,
    )

    return {
        "pr_ref": pr_ref,
        "status": "done",
        "stage": "complete",
        "messages": [
            *state.messages,
            f"Successfully raised draft PR #{pr_ref.pr_id} at {pr_ref.url}",
        ],
    }
