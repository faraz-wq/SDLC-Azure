"""Blast radius scoring node."""

from typing import Any

from agent.core.schemas import BlastRadius
from agent.core.state import RunState


def blast_score_node(state: RunState) -> dict[str, Any]:
    """Score blast radius for each proposed option."""
    scores: list[BlastRadius] = []

    for opt in state.options:
        files_count = len(opt.files_touched)
        api_changes_count = len(opt.expected_api_changes)

        # Check if shared modules are touched
        shared_modules_count = sum(
            1 for f in opt.files_touched if "shared" in f.lower() or "common" in f.lower()
        )

        score = (files_count * 1.0) + (api_changes_count * 3.0) + (shared_modules_count * 2.5)

        scores.append(
            BlastRadius(
                files_count=files_count,
                api_changes_count=api_changes_count,
                shared_modules_count=shared_modules_count,
                score=score,
                components={
                    "files": float(files_count),
                    "api_changes": float(api_changes_count),
                    "shared_modules": float(shared_modules_count),
                },
            )
        )

    return {
        "blast_scores": scores,
        "messages": [
            *state.messages,
            f"Calculated blast radius scores: {[s.score for s in scores]}",
        ],
    }
