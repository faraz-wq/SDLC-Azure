"""Scope guardrail.

REVIEW-CRITICAL FILE: Enforces that code edits stay strictly inside the approved Plan.
Rules:
- Never edit files outside the approved plan's allowed_files.
- Diff line count must not exceed Plan.max_diff_lines.
- Must not be bypassed, loosened, or silenced.
"""

import fnmatch

from agent.core.schemas import Plan


class ScopeViolationError(Exception):
    """Raised when modified files or diff size violates the approved Plan."""

    pass


def check_scope(
    touched_files: list[str],
    diff_lines: int,
    plan: Plan,
) -> None:
    """Validate touched files and diff size against approved plan.

    Raises ScopeViolationError on any violation.
    """
    # 1. Check diff line limit
    if diff_lines > plan.max_diff_lines:
        raise ScopeViolationError(
            f"Diff size ({diff_lines} lines) exceeds approved plan limit "
            f"({plan.max_diff_lines} lines)."
        )

    # 2. Check each touched file against allowed_files globs
    for file_path in touched_files:
        norm_file = file_path.strip().replace("\\", "/")
        matched = False
        for allowed in plan.allowed_files:
            clean_allowed = allowed.strip().replace("\\", "/")
            if fnmatch.fnmatch(norm_file, clean_allowed) or clean_allowed in norm_file:
                matched = True
                break

        if not matched:
            raise ScopeViolationError(
                f"File '{norm_file}' is outside the approved plan allowed_files: "
                f"{plan.allowed_files}"
            )
