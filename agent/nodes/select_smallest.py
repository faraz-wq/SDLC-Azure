"""Select smallest blast radius option node."""

from typing import Any

from agent.core.schemas import Plan
from agent.core.state import RunState


def select_smallest_node(state: RunState) -> dict[str, Any]:
    """Select option with lowest blast radius score and prepare frozen Plan."""
    if not state.options or not state.blast_scores:
        raise ValueError("Cannot select plan: options or blast scores are empty.")

    # Find index of lowest score
    min_idx = 0
    min_score = float("inf")
    for i, blast in enumerate(state.blast_scores):
        if blast.score < min_score:
            min_score = blast.score
            min_idx = i

    chosen_option = state.options[min_idx]
    chosen_blast = state.blast_scores[min_idx]
    rejected_options = [opt for i, opt in enumerate(state.options) if i != min_idx]

    plan = Plan(
        ticket_id=state.ticket_id,
        summary=chosen_option.description,
        chosen_option=chosen_option,
        rejected_options=rejected_options,
        blast=chosen_blast,
        allowed_files=chosen_option.files_touched,
        max_diff_lines=150,
        expected_api_changes=chosen_option.expected_api_changes,
        test_targets=["tests/**/*"],
    )

    return {
        "plan": plan,
        "messages": [
            *state.messages,
            (
                f"Selected smallest option '{chosen_option.id}' "
                f"(blast score: {chosen_blast.score:.1f})."
            ),
        ],
    }
