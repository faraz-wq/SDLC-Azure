from pathlib import Path

from agent.core.schemas import HumanRequest, HumanResponse
from agent.session.manager import SessionManager
from agent.session.models import SessionStatus, TicketRunRecord
from agent.session.project import ProjectManager


def test_project_manager_initialization(tmp_path: Path) -> None:
    pm = ProjectManager(root_dir=tmp_path)
    ctx = pm.initialize()

    assert ctx.dot_agent_dir.exists()
    assert (ctx.dot_agent_dir / "sessions.sqlite").exists()
    assert (ctx.dot_agent_dir / "worktrees").exists()
    assert (ctx.dot_agent_dir / "logs").exists()


def test_ticket_registry_crud(tmp_path: Path) -> None:
    pm = ProjectManager(root_dir=tmp_path)
    pm.initialize()

    # Create run
    record = TicketRunRecord(
        ticket_id=42,
        title="Add auth endpoints",
        branch_name="agent/42-add-auth",
        worktree_path=str(tmp_path / ".agent" / "worktrees" / "42"),
        status=SessionStatus.RUNNING,
        stage="clarify",
    )
    pm.save_ticket_run(record)

    # Read run
    fetched = pm.get_ticket_run(42)
    assert fetched is not None
    assert fetched.ticket_id == 42
    assert fetched.title == "Add auth endpoints"
    assert fetched.status == SessionStatus.RUNNING

    # List runs
    all_runs = pm.list_ticket_runs()
    assert len(all_runs) == 1
    assert all_runs[0].ticket_id == 42

    # Update run with pending request
    record.status = SessionStatus.WAITING_ON_HUMAN
    record.pending_request = HumanRequest(
        session_id="ado-42",
        request_type="questions",
        prompt="Please clarify expiration token duration",
    )
    pm.save_ticket_run(record)

    updated = pm.get_ticket_run(42)
    assert updated is not None
    assert updated.status == SessionStatus.WAITING_ON_HUMAN
    assert updated.pending_request is not None
    assert updated.pending_request.prompt == "Please clarify expiration token duration"


def test_session_manager_api(tmp_path: Path) -> None:
    sm = SessionManager(repo_root=tmp_path)
    sm.init_project()

    record = TicketRunRecord(
        ticket_id=101,
        title="Fix database deadlock",
        branch_name="agent/101-fix-deadlock",
        worktree_path=str(tmp_path / ".agent" / "worktrees" / "101"),
        status=SessionStatus.WAITING_ON_HUMAN,
        stage="plan",
        pending_request=HumanRequest(
            session_id="ado-101",
            request_type="plan_approval",
            prompt="Approve option 1",
        ),
    )
    sm.project.save_ticket_run(record)

    # list_tickets
    tickets = sm.list_tickets()
    assert len(tickets) == 1
    assert tickets[0].ticket_id == 101

    # get_pending
    pending = sm.get_pending(101)
    assert pending is not None
    assert pending.request_type == "plan_approval"

    # submit_response
    response = HumanResponse(
        session_id="ado-101",
        decision="approved",
        feedback="Looks good",
    )
    sm.submit_response(101, response)

    updated_run = sm.project.get_ticket_run(101)
    assert updated_run is not None
    assert updated_run.status == SessionStatus.RUNNING
    assert updated_run.pending_request is None

    # clean_ticket
    sm.clean_ticket(101)
    assert sm.project.get_ticket_run(101) is None
