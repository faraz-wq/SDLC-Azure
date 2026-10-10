from pathlib import Path

import pytest

from agent.session.models import SessionStatus, TicketRunRecord
from agent.session.project import ProjectManager
from agent.ui.tui.app import SDLCApp


@pytest.mark.asyncio
async def test_tui_app_mount(tmp_path: Path) -> None:
    pm = ProjectManager(root_dir=tmp_path)
    pm.initialize()

    record = TicketRunRecord(
        ticket_id=12,
        title="Implement OAuth flow",
        branch_name="agent/12-oauth",
        worktree_path=str(tmp_path / ".agent" / "worktrees" / "12"),
        status=SessionStatus.RUNNING,
        stage="implement",
    )
    pm.save_ticket_run(record)

    app = SDLCApp(repo_root=tmp_path)
    async with app.run_test() as pilot:
        assert pilot.app is not None
        assert "SDLC" in pilot.app.title
