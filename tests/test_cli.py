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

    # Clean with --yes
    clean_res = runner.invoke(app, ["clean", "88", "--yes", "--repo", str(tmp_path)])
    assert clean_res.exit_code == 0
    assert "Cleaned session" in clean_res.stdout

    # Clean non-existent should fail with code 1
    clean_missing = runner.invoke(app, ["clean", "999", "--yes", "--repo", str(tmp_path)])
    assert clean_missing.exit_code == 1

    # Status should now be empty
    status_res = runner.invoke(app, ["status", "--repo", str(tmp_path)])
    assert "No active ticket sessions found" in status_res.stdout


def test_repl_slash_command_filtering_and_completion() -> None:
    from agent.ui.cli.repl import extract_completion, filter_commands

    # Bare slash lists all 8 commands
    all_commands = filter_commands("/")
    assert len(all_commands) == 8

    # Specific slash prefix
    run_commands = filter_commands("/r")
    assert len(run_commands) == 2
    assert run_commands[0][0] == "/run <id>"

    # Non-slash input returns empty
    assert filter_commands("hello") == []

    # Extraction extracts base command with space when args needed
    assert extract_completion("/run <id>") == "/run "
    assert extract_completion("/ado") == "/ado"
