import pytest
from pydantic import ValidationError

from agent.core.schemas import (
    BlastRadius,
    Comment,
    HumanRequest,
    HumanResponse,
    Option,
    Plan,
    RunMetrics,
    Ticket,
)


def test_ticket_schema_valid() -> None:
    ticket = Ticket(
        id=123,
        title="Add auth endpoints",
        description="Add endpoints for user login and signup",
        acceptance_criteria=["Must return 200 on valid credentials", "Must return 401 on invalid"],
        comments=[Comment(id="c1", author="Tester", body="Please include refresh token")],
        tags=["auth", "api"],
    )
    assert ticket.id == 123
    assert len(ticket.acceptance_criteria) == 2
    assert len(ticket.comments) == 1
    assert ticket.comments[0].author == "Tester"


def test_ticket_schema_invalid() -> None:
    with pytest.raises(ValidationError):
        # Missing required id and title
        Ticket.model_validate({"description": "incomplete"})


def test_plan_schema_valid() -> None:
    option = Option(
        id="opt-1",
        description="Modify auth controller and token service",
        files_touched=["src/Auth/AuthController.cs", "src/Auth/TokenService.cs"],
        expected_api_changes=["POST /api/auth/refresh"],
    )
    blast = BlastRadius(
        files_count=2,
        api_changes_count=1,
        shared_modules_count=0,
        score=3.5,
    )
    plan = Plan(
        ticket_id=123,
        summary="Implement token refresh endpoint",
        chosen_option=option,
        rejected_options=[],
        blast=blast,
        allowed_files=["src/Auth/**"],
        max_diff_lines=150,
        expected_api_changes=["POST /api/auth/refresh"],
        test_targets=["tests/AuthTests/**"],
    )
    assert plan.ticket_id == 123
    assert plan.chosen_option.id == "opt-1"
    assert plan.max_diff_lines == 150


def test_human_request_response_flow() -> None:
    req = HumanRequest(
        session_id="ado-123",
        request_type="questions",
        prompt="Clarify token expiration duration",
        options=["15m", "1h", "24h"],
    )
    assert req.request_type == "questions"

    resp = HumanResponse(
        session_id="ado-123",
        decision="answered",
        answers={"token_expiration": "1h"},
    )
    assert resp.decision == "answered"
    assert resp.answers["token_expiration"] == "1h"


def test_run_metrics_defaults() -> None:
    metrics = RunMetrics(
        run_id="run-001",
        ticket_id=123,
        clarification_asked=True,
        questions_count=2,
        iterations_count=1,
        wall_time_seconds=12.5,
        outcome="success",
    )
    assert metrics.run_id == "run-001"
    assert metrics.outcome == "success"
