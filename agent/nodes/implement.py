"""Implement node: works in isolated git worktree with caps, limits, and Pi coding agent."""

import shutil
from pathlib import Path
from typing import Any

from agent.coding.pi_agent import PiCodingAgent
from agent.core.protocols import CodingAgent
from agent.core.schemas import CodingTask, Limits
from agent.core.state import RunState
from agent.guards.diff_cap import check_diff_cap
from agent.guards.iteration_cap import check_iteration_cap
from agent.tools.git_worktree import create_worktree, get_diff


def implement_node(
    state: RunState,
    repo_root: Path | None = None,
    coding_agent: CodingAgent | None = None,
) -> dict[str, Any]:
    """Execute code modification inside isolated worktree using the Pi coding agent."""
    root = repo_root or Path.cwd()
    new_iteration = state.iteration + 1
    check_iteration_cap(new_iteration, max_iterations=5)

    # Allocate or reuse worktree
    slug = state.ticket.title if state.ticket else "feature"
    wt_path, branch_name = create_worktree(root, state.ticket_id, slug)

    # Invoke CodingAgent (PiCodingAgent) to perform real edits in the worktree
    agent = coding_agent or PiCodingAgent()
    prompt = (
        f"Implement ticket #{state.ticket_id}: {state.ticket.title if state.ticket else ''}\n"
        f"Acceptance criteria: {state.ticket.acceptance_criteria if state.ticket else []}"
    )
    allowed = state.plan.allowed_files if state.plan else []
    task = CodingTask(
        task_id=f"impl-{state.ticket_id}-{new_iteration}",
        prompt=prompt,
        allowed_files=allowed,
        limits=Limits(max_iterations=1, timeout_seconds=180),
    )
    error_msg: str | None = None
    try:
        res = agent.run(task, wt=wt_path, limits=task.limits)
        if not res.success and shutil.which("pi") is not None:
            error_msg = f"Coding agent returned failure for task {task.task_id}"
    except Exception as e:
        if shutil.which("pi") is not None:
            error_msg = f"Coding agent error: {e}"

    diff_text = get_diff(wt_path)
    diff_lines = len(diff_text.splitlines())
    check_diff_cap(diff_lines, max_cap=300)

    messages = [
        *state.messages,
        f"Implemented iteration {new_iteration} in worktree {wt_path} (branch: {branch_name}).",
    ]
    if error_msg:
        messages.append(f"Warning: {error_msg}")

    return {
        "iteration": new_iteration,
        "worktree_path": str(wt_path),
        "branch_name": branch_name,
        "diff": diff_text,
        "stage": "verify" if not error_msg else "failed",
        "error": error_msg,
        "messages": messages,
    }
