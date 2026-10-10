"""Interactive OpenCode-style Terminal UI for SDLC Agent.

Strict architectural rule: UI code talks only to agent/session/.
It never imports nodes, adapters, or connectors.
"""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, Static

from agent.core.schemas import HumanResponse
from agent.session.manager import SessionManager
from agent.session.models import SessionStatus, TicketRunRecord


class TicketItem(ListItem):
    """List item representing a single tracked ticket session."""

    def __init__(self, record: TicketRunRecord) -> None:
        super().__init__()
        self.record = record

    def compose(self) -> ComposeResult:
        status_style = "green" if self.record.status == SessionStatus.DONE else "cyan"
        if self.record.status == SessionStatus.WAITING_ON_HUMAN:
            status_style = "red bold"

        st = self.record.status.value
        title_trunc = self.record.title[:20]
        label = f"#{self.record.ticket_id} [{status_style}]{st}[/] - {title_trunc}"
        yield Label(label)


class SDLCApp(App[None]):
    """OpenCode-style interactive TUI application for the SDLC Agent."""

    TITLE = "Azure DevOps SDLC Agent"
    SUB_TITLE = "Local Workspace & Session Manager"

    CSS = """
    Screen {
        background: #111827;
        color: #f3f4f6;
    }
    #sidebar {
        width: 38;
        background: #1f2937;
        border-right: solid #374151;
        padding: 1;
    }
    #sidebar-title {
        text-style: bold;
        color: #38bdf8;
        margin-bottom: 1;
    }
    #main {
        padding: 1 2;
        background: #111827;
    }
    .card {
        background: #1f2937;
        border: solid #374151;
        padding: 1 2;
        margin-bottom: 1;
    }
    .title {
        text-style: bold;
        color: #38bdf8;
        margin-bottom: 1;
    }
    .label {
        color: #9ca3af;
    }
    .value {
        color: #f3f4f6;
        text-style: bold;
    }
    #questions-container {
        margin-top: 1;
        background: #374151;
        padding: 1;
        border: solid #f59e0b;
    }
    Button {
        margin-top: 1;
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("r", "refresh_sessions", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, repo_root: Path | None = None) -> None:
        super().__init__()
        self.repo_root = repo_root or Path.cwd()
        self.session_mgr = SessionManager(repo_root=self.repo_root)
        self.current_ticket: TicketRunRecord | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("ACTIVE SESSIONS", id="sidebar-title")
                yield ListView(id="sessions-list")
                yield Button("Refresh (r)", id="btn-refresh", variant="primary")
            with VerticalScroll(id="main"):
                with Container(classes="card", id="details-card"):
                    yield Label("Select a session from the left sidebar.", id="details-text")
                with Vertical(id="action-pane"):
                    pass
        yield Footer()

    def on_mount(self) -> None:
        """Mount event: load active sessions."""
        self.action_refresh_sessions()

    def action_refresh_sessions(self) -> None:
        """Fetch and populate tickets in the sidebar."""
        list_view = self.query_one("#sessions-list", ListView)
        list_view.clear()

        tickets = self.session_mgr.list_tickets()
        if not tickets:
            list_view.append(ListItem(Label("[dim]No active sessions[/dim]")))
            return

        for t in tickets:
            list_view.append(TicketItem(t))

        if tickets and not self.current_ticket:
            self.display_ticket(tickets[0])

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Triggered when a ticket is selected from the list."""
        if isinstance(event.item, TicketItem):
            self.display_ticket(event.item.record)

    def display_ticket(self, record: TicketRunRecord) -> None:
        """Display ticket details and interactive action forms."""
        self.current_ticket = record
        details_text = self.query_one("#details-text", Label)
        details_text.update(
            f"[bold cyan]Ticket #{record.ticket_id}:[/bold cyan] {record.title}\n"
            f"[dim]Status:[/dim] [bold]{record.status.value}[/bold] | "
            f"[dim]Stage:[/dim] {record.stage}\n"
            f"[dim]Branch:[/dim] {record.branch_name}\n"
            f"[dim]Worktree:[/dim] {record.worktree_path}\n"
            f"[dim]PR Link:[/dim] {record.pr_url or 'None'}"
        )

        action_pane = self.query_one("#action-pane", Vertical)
        action_pane.remove_children()

        if record.status == SessionStatus.WAITING_ON_HUMAN and record.pending_request:
            req = record.pending_request
            action_pane.mount(
                Static(
                    f"[bold yellow]⚠ ACTION REQUIRED: {req.request_type.upper()}[/bold yellow]\n"
                    f"{req.prompt}",
                    classes="card",
                )
            )

            # If clarification questions, render an input form
            if req.options:
                for idx, opt in enumerate(req.options):
                    action_pane.mount(Label(f"Q{idx + 1}: {opt}", classes="label"))
                    action_pane.mount(
                        Input(placeholder="Type your answer here...", id=f"ans-input-{idx}")
                    )

                action_pane.mount(
                    Button("Submit Answers", id="btn-submit-answers", variant="success")
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press actions."""
        if event.button.id == "btn-refresh":
            self.action_refresh_sessions()
        elif event.button.id == "btn-submit-answers" and self.current_ticket:
            answers: dict[str, str] = {}
            if self.current_ticket.pending_request and self.current_ticket.pending_request.options:
                for idx, opt in enumerate(self.current_ticket.pending_request.options):
                    try:
                        inp = self.query_one(f"#ans-input-{idx}", Input)
                        answers[opt] = inp.value
                    except Exception:
                        pass

            response = HumanResponse(
                session_id=f"ado-{self.current_ticket.ticket_id}",
                decision="answered",
                answers=answers,
            )
            self.session_mgr.submit_response(self.current_ticket.ticket_id, response)
            self.notify(f"Submitted answers for ticket #{self.current_ticket.ticket_id}!")
            self.action_refresh_sessions()


def run_tui(repo_root: Path | None = None) -> None:
    """Launch the interactive TUI application."""
    app = SDLCApp(repo_root=repo_root)
    app.run()
