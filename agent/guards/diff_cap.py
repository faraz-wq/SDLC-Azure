"""Diff cap guardrail.

REVIEW-CRITICAL FILE: Enforces bounded diff effort.
"""


class DiffCapViolationError(Exception):
    """Raised when diff exceeds hard iteration/run limits."""

    pass


def check_diff_cap(diff_lines: int, max_cap: int = 300) -> None:
    """Validate that the diff line count does not exceed hard cap."""
    if diff_lines > max_cap:
        raise DiffCapViolationError(
            f"Total diff ({diff_lines} lines) exceeds maximum allowed cap of {max_cap} lines."
        )
