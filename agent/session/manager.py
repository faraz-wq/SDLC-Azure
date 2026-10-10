"""Session manager API consumed by CLI and interactive channels."""

import shutil
import sqlite3
from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver

from agent.connectors.pr_host_azure import AzurePRHost
from agent.connectors.ticket_source_azure import AzureTicketSource
from agent.core.protocols import HumanChannel
from agent.core.schemas import HumanRequest, HumanResponse
from agent.core.state import RunState
from agent.graph import create_full_sdlc_graph
from agent.llm.opencode_client import OpenCodeClient
from agent.session.models import ProjectContext, SessionStatus, TicketRunRecord
from agent.session.project import ProjectManager


class LocalSessionChannel(HumanChannel):
    """Stores human interaction requests in local session context."""

    def __init__(self) -> None:
        self.last_request: HumanRequest | None = None

    def ask(self, session_id: str, request: HumanRequest) -> None:
        self.last_request = request

    def collect(self, session_id: str) -> HumanResponse | None:
        return None


class SessionManager:
    """Public session management API over local project workspace."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()
        self.project = ProjectManager(root_dir=self.repo_root)

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

    def run_ticket(self, ticket_id: int, dry_run: bool = False) -> TicketRunRecord:
        """Execute or resume the state machine for a work item."""
        self.init_project()
        run = self.project.get_ticket_run(ticket_id)
        if not run:
            run = TicketRunRecord(
                ticket_id=ticket_id,
                title=f"Work Item #{ticket_id}",
                branch_name=f"agent/{ticket_id}-work",
                worktree_path=str(self.project.worktrees_dir / str(ticket_id)),
                status=SessionStatus.RUNNING,
                stage="ingest",
            )
            self.project.save_ticket_run(run)

        # Initialize connectors and channel
        channel = LocalSessionChannel()
        ticket_source = AzureTicketSource(dry_run=dry_run)
        pr_host = AzurePRHost(dry_run=dry_run)
        llm = OpenCodeClient()

        conn = sqlite3.connect(self.project.db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)
        checkpointer.setup()

        graph = create_full_sdlc_graph(
            ticket_source=ticket_source,
            pr_host=pr_host,
            llm=llm,
            channel=channel,
            checkpointer=checkpointer,
            repo_root=self.repo_root,
        )

        config: RunnableConfig = {"configurable": {"thread_id": f"ado-{ticket_id}"}}

        # Check existing state in checkpointer
        existing_state = graph.get_state(config)
        result: dict[str, Any]
        if existing_state and existing_state.values:
            # Resuming
            graph.update_state(config, {"status": "running"})
            result = graph.invoke(None, config=config)
        else:
            initial = RunState(run_id=f"run-{ticket_id}", ticket_id=ticket_id)
            result = graph.invoke(initial, config=config)

        conn.close()

        # Update and save ticket run record
        status_val = str(result.get("status", "running"))
        if status_val == "waiting_on_human":
            run.status = SessionStatus.WAITING_ON_HUMAN
        elif status_val in [s.value for s in SessionStatus]:
            run.status = SessionStatus(status_val)
        else:
            run.status = SessionStatus.RUNNING

        run.stage = str(result.get("stage", run.stage))

        ticket_obj = result.get("ticket")
        if ticket_obj:
            run.title = ticket_obj.title

        pr_ref_obj = result.get("pr_ref")
        if pr_ref_obj:
            run.pr_id = pr_ref_obj.pr_id
            run.pr_url = pr_ref_obj.url

        if channel.last_request:
            run.pending_request = channel.last_request

        self.project.save_ticket_run(run)
        return run
