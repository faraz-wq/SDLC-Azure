"""Iteration cap guardrail.

REVIEW-CRITICAL FILE: Prevents infinite agent self-correction loops.
"""


class IterationCapViolationError(Exception):
    """Raised when implement-verify loop exceeds iteration cap."""

    pass


def check_iteration_cap(current_iteration: int, max_iterations: int = 5) -> None:
    """Validate that the current loop iteration has not exceeded the hard limit."""
    if current_iteration > max_iterations:
        raise IterationCapViolationError(
            f"Execution exceeded maximum loop iteration cap of {max_iterations} "
            f"(current: {current_iteration})."
        )
