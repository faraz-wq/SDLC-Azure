"""Implement node: works in isolated git worktree with caps and limits."""

from pathlib import Path
from typing import Any

from agent.core.state import RunState
from agent.guards.diff_cap import check_diff_cap
from agent.guards.iteration_cap import check_iteration_cap
from agent.tools.git_worktree import create_worktree, get_diff


def implement_node(state: RunState, repo_root: Path | None = None) -> dict[str, Any]:
    """Execute code modification inside isolated worktree under strict iteration caps."""
    root = repo_root or Path.cwd()
    new_iteration = state.iteration + 1
    check_iteration_cap(new_iteration, max_iterations=5)

    # Allocate or reuse worktree
    slug = state.ticket.title if state.ticket else "feature"
    wt_path, branch_name = create_worktree(root, state.ticket_id, slug)

    diff_text = get_diff(wt_path)
    diff_lines = len(diff_text.splitlines())
    check_diff_cap(diff_lines, max_cap=300)

    return {
        "iteration": new_iteration,
        "worktree_path": str(wt_path),
        "branch_name": branch_name,
        "diff": diff_text,
        "stage": "verify",
        "messages": [
            *state.messages,
            f"Implemented iteration {new_iteration} in worktree {wt_path} (branch: {branch_name}).",
        ],
    }
