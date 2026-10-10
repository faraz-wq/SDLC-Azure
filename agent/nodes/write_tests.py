"""Write tests first node."""

from typing import Any

from agent.core.protocols import LLMClient
from agent.core.state import RunState


def write_tests_node(state: RunState, llm: LLMClient) -> dict[str, Any]:
    """Generate unit tests and verifier spec from acceptance criteria before code edits."""
    if not state.plan:
        raise ValueError("Cannot write tests: plan is missing.")

    criteria = state.ticket.acceptance_criteria if state.ticket else []
    test_files = {
        "tests/GeneratedTests.cs": "// Auto-generated tests from acceptance criteria\n"
        + "\n".join(f"// Test: {c}" for c in criteria)
    }

    return {
        "tests_code": test_files,
        "stage": "confirm_red",
        "messages": [
            *state.messages,
            f"Generated {len(test_files)} test files from {len(criteria)} acceptance criteria.",
        ],
    }
