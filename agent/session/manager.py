"""Session manager API consumed by CLI and interactive channels."""

import shutil
from pathlib import Path

from agent.core.schemas import HumanRequest, HumanResponse
from agent.session.models import ProjectContext, SessionStatus, TicketRunRecord
from agent.session.project import ProjectManager


class SessionManager:
    """Public session management API over local project workspace."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.project = ProjectManager(root_dir=repo_root)

    def init_project(self) -> ProjectContext:
        """Initialize the local agent workspace."""
        return self.project.initialize()

    def list_tickets(self) -> list[TicketRunRecord]:
        """List all ticket sessions in flight or completed."""
        return self.project.list_ticket_runs()

    def get_pending(self, ticket_id: int) -> HumanRequest | None:
        """Get the pending human interrupt request for a ticket if any."""
        run = self.project.get_ticket_run(ticket_id)
        if run and run.status == SessionStatus.WAITING_ON_HUMAN:
            return run.pending_request
        return None

    def submit_response(self, ticket_id: int, response: HumanResponse) -> None:
        """Submit a human response to resume a waiting session."""
        run = self.project.get_ticket_run(ticket_id)
        if not run:
            raise ValueError(f"No active session found for ticket {ticket_id}")

        # Update run status and clear pending request
        run.status = SessionStatus.RUNNING
        run.pending_request = None
        self.project.save_ticket_run(run)

    def clean_ticket(self, ticket_id: int, remove_worktree: bool = True) -> None:
        """Prune ticket registry record and optionally delete local worktree folder."""
        run = self.project.get_ticket_run(ticket_id)
        if run and remove_worktree:
            wt_path = Path(run.worktree_path)
            if wt_path.exists():
                shutil.rmtree(wt_path, ignore_errors=True)

        self.project.delete_ticket_run(ticket_id)
