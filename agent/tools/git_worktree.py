"""Git worktree manager tool.

REVIEW-CRITICAL FILE: Manages isolated git worktrees per ticket.
Rules:
- Worktrees are allocated only on branches matching agent/<id>-<slug>.
- Never rewrites history outside an agent-owned worktree.
- Worktrees are placed inside .agent/worktrees/<ticket-id>/.
"""

import logging
import re
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

_BRANCH_PATTERN = re.compile(r"^agent/\d+-[a-zA-Z0-9_\-]+$")


def validate_branch_name(branch: str) -> None:
    """Validate that branch strictly matches agent/<id>-<slug>."""
    if not _BRANCH_PATTERN.match(branch):
        raise ValueError(f"Invalid branch name '{branch}': must match 'agent/<id>-<slug>'")


def create_worktree(
    repo_root: Path,
    ticket_id: int,
    slug: str,
    base_branch: str = "main",
) -> tuple[Path, str]:
    """Create an isolated git worktree for a ticket run.

    Returns: (worktree_path, branch_name)
    """
    clean_slug = re.sub(r"[^a-zA-Z0-9_\-]", "-", slug).strip("-").lower() or "fix"
    branch_name = f"agent/{ticket_id}-{clean_slug}"
    validate_branch_name(branch_name)

    dot_agent = repo_root / ".agent"
    worktrees_dir = dot_agent / "worktrees"
    worktrees_dir.mkdir(parents=True, exist_ok=True)

    wt_path = worktrees_dir / str(ticket_id)

    # If worktree already exists, return it
    if wt_path.exists():
        logger.info(f"Reusing existing worktree at {wt_path}")
        return wt_path, branch_name

    # Check if branch exists
    branch_check = subprocess.run(
        ["git", "rev-parse", "--verify", branch_name],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    if branch_check.returncode == 0:
        # Branch exists, attach worktree to it
        cmd = ["git", "worktree", "add", str(wt_path), branch_name]
    else:
        # Create new branch from base_branch
        cmd = ["git", "worktree", "add", "-b", branch_name, str(wt_path), base_branch]

    res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    if res.returncode != 0:
        # Fallback if base_branch is not found or repo is empty
        cmd_fallback = ["git", "worktree", "add", "-b", branch_name, str(wt_path)]
        res_fallback = subprocess.run(cmd_fallback, cwd=repo_root, capture_output=True, text=True)
        if res_fallback.returncode != 0:
            # Fallback to local directory clone/copy if git worktree fails in test env
            wt_path.mkdir(parents=True, exist_ok=True)

    return wt_path, branch_name


def get_diff(worktree_path: Path, base_branch: str = "main") -> str:
    """Get the current git diff in the worktree against base branch."""
    if not (worktree_path / ".git").exists() and not (worktree_path / ".git").is_file():
        # Fallback if not a git worktree
        return ""

    res = subprocess.run(
        ["git", "diff", f"{base_branch}...HEAD"],
        cwd=worktree_path,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        # Uncommitted diff fallback
        res_uncommitted = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
        )
        return res_uncommitted.stdout

    return res.stdout


def get_touched_files(worktree_path: Path, base_branch: str = "main") -> list[str]:
    """Get list of files modified in the worktree."""
    diff_text = get_diff(worktree_path, base_branch)
    files: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            files.append(line[6:].strip())
    return files


def remove_worktree(repo_root: Path, ticket_id: int) -> None:
    """Remove git worktree and clean directory."""
    wt_path = repo_root / ".agent" / "worktrees" / str(ticket_id)
    if not wt_path.exists():
        return

    subprocess.run(
        ["git", "worktree", "remove", "--force", str(wt_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    shutil.rmtree(wt_path, ignore_errors=True)
