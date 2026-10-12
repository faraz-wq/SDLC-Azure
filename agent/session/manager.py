"""Session manager API consumed by CLI and interactive channels."""

import shutil
import sqlite3
import subprocess
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

    def chat(self, message: str) -> str:
        """Send a message to the AI coding assistant and get a response."""
        prompt = (
            "You are an expert Azure DevOps SDLC coding assistant. "
            "Help the developer inspect code, run SDLC workflows on Azure DevOps work items, "
            "and navigate their repository.\n\n"
            f"User message: {message}"
        )
        # Try local Pi agent first (which is authenticated and active)
        try:
            pi_bin = shutil.which("pi") or "pi"
            res = subprocess.run(
                [pi_bin, "-p", prompt],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

        # Fallback to OpenCodeClient
        llm = OpenCodeClient()
        try:
            resp = llm.complete(
                role="clarify",
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.text.strip()
        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                return (
                    "**Authentication Required:** Could not communicate with AI assistant.\n\n"
                    "Reason: HTTP 401 Unauthorized (Invalid or missing `OPENCODE_API_KEY`).\n"
                    "Next step: Set your `OPENCODE_API_KEY` in `.env` to enable chat."
                )
            return f"Error communicating with AI assistant: {e}"

    def execute_command(self, command_line: str) -> str:
        """Execute a slash command and return the formatted response."""
        parts = command_line.strip().split()
        if not parts:
            return ""

        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("/help", "/?"):
            return (
                "**Available Slash Commands:**\n"
                "- `/help`: Show this command summary.\n"
                "- `/ado`: Show current Azure DevOps connection status.\n"
                "- `/ado setup <org> <project> [repo]`: Update Azure DevOps details in `.env`.\n"
                "- `/run <ticket_id> [--dry-run]`: Run SDLC pipeline on a work item.\n"
                "- `/status` or `/list`: List active ticket sessions and branches.\n"
                "- `/clean <ticket_id>`: Remove ticket session and local worktree.\n"
                "- `/exit` or `/quit`: Exit the application."
            )

        if cmd == "/ado":
            if len(args) >= 3 and args[0].lower() == "setup":
                org = args[1]
                project = args[2]
                repo = args[3] if len(args) > 3 else project
                env_path = self.repo_root / ".env"
                lines: list[str] = []
                if env_path.exists():
                    lines = env_path.read_text().splitlines()

                keys_to_set = {
                    "AZURE_DEVOPS_ORG": org,
                    "AZURE_DEVOPS_PROJECT": project,
                    "AZURE_DEVOPS_REPO": repo,
                }
                new_lines: list[str] = []
                found_keys: set[str] = set()
                for line in lines:
                    k = line.split("=", 1)[0].strip()
                    if k in keys_to_set:
                        new_lines.append(f"{k}={keys_to_set[k]}")
                        found_keys.add(k)
                    else:
                        new_lines.append(line)
                for k, v in keys_to_set.items():
                    if k not in found_keys:
                        new_lines.append(f"{k}={v}")

                env_path.write_text("\n".join(new_lines) + "\n")
                return (
                    "Azure DevOps configuration updated:\n"
                    f"- Org: `{org}`\n- Project: `{project}`\n- Repo: `{repo}`"
                )

            # Check status
            import os

            org = os.getenv("AZURE_DEVOPS_ORG", "")
            project = os.getenv("AZURE_DEVOPS_PROJECT", "")
            repo = os.getenv("AZURE_DEVOPS_REPO", "")
            pat = os.getenv("AZURE_DEVOPS_PAT", "")
            pat_status = f"Configured ({len(pat)} chars)" if pat else "Missing"

            status_msg = (
                f"**Azure DevOps Status:**\n"
                f"- Organization: `{org or 'Not set'}`\n"
                f"- Project: `{project or 'Not set'}`\n"
                f"- Repository: `{repo or 'Not set'}`\n"
                f"- PAT Status: {pat_status}\n"
            )

            # Test connection if credentials exist
            if org and project and pat:
                try:
                    AzureTicketSource()
                    status_msg += "\nConnection verified successfully."
                except Exception as e:
                    status_msg += f"\nConnection test failed: {e}"
            else:
                status_msg += "\nTo configure, run `/ado setup <org> <project> [repo]`."
            return status_msg

        if cmd == "/run":
            if not args:
                return "Usage: `/run <ticket_id> [--dry-run]`"
            try:
                ticket_id = int(args[0])
            except ValueError:
                return f"Invalid ticket ID: `{args[0]}`. Must be an integer."

            dry_run = "--dry-run" in args
            record = self.run_ticket(ticket_id, dry_run=dry_run)
            output = (
                f"**Ticket #{record.ticket_id} Execution Result:**\n"
                f"- Title: {record.title}\n"
                f"- Status: `{record.status.value}`\n"
                f"- Stage: `{record.stage}`\n"
                f"- Branch: `{record.branch_name}`\n"
            )
            if record.pending_request:
                req_type = record.pending_request.request_type
                output += (
                    f"\n[WAITING] **Waiting on Human Input ({req_type}):**\n"
                    f"{record.pending_request.prompt}\n"
                )
                if record.pending_request.options:
                    output += "\nOptions:\n" + "\n".join(
                        f"- {o}" for o in record.pending_request.options
                    )
            elif record.pr_url:
                output += f"\n**Draft PR Created:** {record.pr_url}"
            return output

        if cmd in ("/status", "/list"):
            tickets = self.list_tickets()
            if not tickets:
                return "No active or recorded ticket sessions found in workspace."
            lines = ["**Active Sessions:**"]
            for t in tickets:
                pending = (
                    f" (Waiting: {t.pending_request.request_type})" if t.pending_request else ""
                )
                branch_info = f"Branch: `{t.branch_name}`"
                lines.append(
                    f"- `#{t.ticket_id}` [{t.status.value}] {t.title} - {branch_info}{pending}"
                )
            return "\n".join(lines)

        if cmd == "/clean":
            if not args:
                return "Usage: `/clean <ticket_id>`"
            try:
                t_id = int(args[0])
            except ValueError:
                return f"Invalid ticket ID: `{args[0]}`."
            if not self.project.get_ticket_run(t_id):
                return f"Ticket session #{t_id} does not exist."
            self.clean_ticket(t_id, remove_worktree=True)
            return f"Cleaned session and worktree for ticket #{t_id}."

        import difflib

        known_cmds = ["/help", "/ado", "/run", "/status", "/list", "/clean", "/exit", "/quit"]
        matches = difflib.get_close_matches(cmd, known_cmds, n=1, cutoff=0.6)
        if matches:
            return (
                f"Unknown command: `{cmd}`. Did you mean `{matches[0]}`?\n"
                "Type `/help` for available commands."
            )

        return f"Unknown command: `{cmd}`. Type `/help` for available commands."
