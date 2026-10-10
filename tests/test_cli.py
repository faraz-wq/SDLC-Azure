from pathlib import Path

from typer.testing import CliRunner

from agent.session.models import SessionStatus, TicketRunRecord
from agent.session.project import ProjectManager
from agent.ui.cli.main import app

runner = CliRunner()


def test_cli_init_command(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "Initialized agent workspace" in result.stdout
    assert (tmp_path / ".agent").exists()


def test_cli_status_command(tmp_path: Path) -> None:
    pm = ProjectManager(root_dir=tmp_path)
    pm.initialize()

    record = TicketRunRecord(
        ticket_id=77,
        title="Add user avatars",
        branch_name="agent/77-avatars",
        worktree_path=str(tmp_path / ".agent" / "worktrees" / "77"),
        status=SessionStatus.RUNNING,
        stage="implement",
    )
    pm.save_ticket_run(record)

    result = runner.invoke(app, ["status", "--repo", str(tmp_path)], env={"COLUMNS": "160"})
    assert result.exit_code == 0
    assert "77" in result.stdout
    assert "Add user avatars" in result.stdout
    assert "agent/77-avatars" in result.stdout


def test_cli_attach_and_clean_commands(tmp_path: Path) -> None:
    pm = ProjectManager(root_dir=tmp_path)
    pm.initialize()

    record = TicketRunRecord(
        ticket_id=88,
        title="Fix memory leak",
        branch_name="agent/88-mem-leak",
        worktree_path=str(tmp_path / ".agent" / "worktrees" / "88"),
        status=SessionStatus.RUNNING,
        stage="verify",
    )
    pm.save_ticket_run(record)

    # Attach
    attach_res = runner.invoke(app, ["attach", "88", "--repo", str(tmp_path)])
    assert attach_res.exit_code == 0
    assert "Ticket #88" in attach_res.stdout
    assert "Fix memory leak" in attach_res.stdout

    # Clean
    clean_res = runner.invoke(app, ["clean", "88", "--repo", str(tmp_path)])
    assert clean_res.exit_code == 0
    assert "Cleaned session" in clean_res.stdout

    # Status should now be empty
    status_res = runner.invoke(app, ["status", "--repo", str(tmp_path)])
    assert "No active ticket sessions found" in status_res.stdout
