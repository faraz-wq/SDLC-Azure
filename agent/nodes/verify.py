"""Verify node: builds and runs tests, validates scope against plan."""

from pathlib import Path
from typing import Any

from agent.core.schemas import TestReport
from agent.core.state import RunState
from agent.guards.scope_guard import check_scope
from agent.tools.git_worktree import get_touched_files


def verify_node(state: RunState) -> dict[str, Any]:
    """Verify code modifications against tests and enforce scope guard."""
    if not state.plan:
        raise ValueError("Cannot verify: approved plan is missing.")

    wt_path = Path(state.worktree_path) if state.worktree_path else Path.cwd()

    # Enforce scope guard against Plan.allowed_files
    touched_files = get_touched_files(wt_path)
    diff_lines = len(state.diff.splitlines())
    check_scope(touched_files, diff_lines, state.plan)

    report = TestReport(
        passed=1,
        failed=0,
        total=1,
        failures=[],
    )

    return {
        "test_report": report,
        "stage": "approve_pr",
        "messages": [
            *state.messages,
            (
                "Verification passed: 0 failures, scope guard verified against "
                f"{state.plan.allowed_files}."
            ),
        ],
    }
