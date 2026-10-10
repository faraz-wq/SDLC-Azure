import pytest

from agent.core.schemas import BlastRadius, Option, Plan
from agent.guards.scope_guard import ScopeViolationError, check_scope


def _make_plan(allowed_files: list[str], max_diff_lines: int = 300) -> Plan:
    return Plan(
        ticket_id=1,
        summary="test",
        chosen_option=Option(id="opt-1", description="d", files_touched=allowed_files),
        blast=BlastRadius(files_count=1, api_changes_count=0, shared_modules_count=0, score=1.0),
        allowed_files=allowed_files,
        max_diff_lines=max_diff_lines,
    )


def test_scope_guard_allowed_files_pass() -> None:
    plan = _make_plan(["src/**/*.cs", "tests/**/*.cs"])
    check_scope(["src/Controllers/AuthController.cs", "tests/AuthTests.cs"], 50, plan)


def test_scope_guard_diff_lines_exceeded() -> None:
    plan = _make_plan(["src/**/*.cs"], max_diff_lines=100)
    with pytest.raises(ScopeViolationError, match="exceeds approved plan limit"):
        check_scope(["src/App.cs"], 101, plan)


def test_scope_guard_file_outside_plan() -> None:
    plan = _make_plan(["src/**/*.cs"])
    with pytest.raises(ScopeViolationError, match="outside the approved plan"):
        check_scope(["infra/terraform.tf"], 10, plan)


def test_scope_guard_substring_loophole() -> None:
    """'src/api' as allowed must NOT match 'src/api-evil/bad.cs' via substring rule."""
    plan = _make_plan(["src/api"])
    with pytest.raises(ScopeViolationError):
        check_scope(["src/api-evil/bad.cs"], diff_lines=1, plan=plan)


def test_scope_guard_windows_path_separator_bypass() -> None:
    """Backslash paths must not bypass scope guard via prefix substring."""
    plan = _make_plan(["src/safe"])
    with pytest.raises(ScopeViolationError):
        check_scope(["src\\safe-zone\\evil.cs"], diff_lines=1, plan=plan)
