"""Pi Agent implementation of the CodingAgent protocol.

Rule: Integrates the real Pi CLI for inner-loop code generation,
unit test writing, and bug fixing inside isolated git worktrees.
"""

import shutil
import subprocess
from pathlib import Path

from agent.core.protocols import CodingAgent
from agent.core.schemas import CodingResult, CodingTask, Limits
from agent.tools.git_worktree import get_diff


class PiCodingAgent(CodingAgent):
    """Executes coding tasks using the local Pi agent CLI."""

    def __init__(self, pi_binary: str = "pi") -> None:
        self.pi_binary = shutil.which(pi_binary) or "pi"

    def run(self, task: CodingTask, wt: Path, limits: Limits) -> CodingResult:
        """Run the Pi agent on a coding task inside a specific worktree directory."""
        allowed_str = ", ".join(task.allowed_files) if task.allowed_files else "any repo file"
        instruction = (
            f"You are modifying the codebase to implement task: {task.task_id}.\n"
            f"Task Prompt: {task.prompt}\n"
            f"Strict Constraint: You may ONLY modify the following files: {allowed_str}.\n"
            "Do not modify any other files."
        )

        try:
            res = subprocess.run(
                [self.pi_binary, "-p", instruction],
                cwd=str(wt),
                capture_output=True,
                text=True,
                timeout=limits.timeout_seconds,
            )
            success = res.returncode == 0
        except Exception:
            success = False

        diff_text = get_diff(wt)
        return CodingResult(
            iterations=1,
            tokens=0,
            final_diff=diff_text,
            success=success,
        )

