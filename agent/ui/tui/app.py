"""Interactive OpenCode-style Terminal UI for Azure DevOps SDLC Agent.

Strict architectural rule: UI code talks only to agent/session/.
It never imports nodes, adapters, or connectors.
"""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Markdown,
    Static,
)

from agent.core.schemas import HumanResponse
from agent.session.manager import SessionManager
from agent.session.models import SessionStatus, TicketRunRecord


class TicketItem(ListItem):
    """List item representing a single tracked ticket session in the sidebar."""

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


class ChatMessageWidget(Static):
    """Single chat message bubble widget."""

    def __init__(self, author: str, content: str, is_user: bool = False) -> None:
        super().__init__(classes="message-user" if is_user else "message-agent")
        self.author = author
        self.msg_content = content

    def compose(self) -> ComposeResult:
        author_color = (
            "cyan" if self.author == "You" else ("green" if self.author == "System" else "magenta")
        )
        yield Label(
            f"[bold {author_color}]{self.author}[/bold {author_color}]:", classes="message-author"
        )
        yield Markdown(self.msg_content)


class SDLCApp(App[None]):
    """Interactive conversational TUI for the Azure DevOps SDLC Agent."""

    TITLE = "Azure DevOps SDLC Agent"
    SUB_TITLE = "Interactive Coding & SDLC Assistant"

    CSS = """
    Screen {
        background: #0f172a;
        color: #f8fafc;
    }
    #sidebar {
        width: 32;
        background: #1e293b;
        border-right: solid #334155;
        padding: 1;
    }
    #sidebar-title {
        text-style: bold;
        color: #38bdf8;
        margin-bottom: 1;
    }
    #main-chat {
        background: #0f172a;
        padding: 1 2;
    }
    #chat-scroll {
        height: 1fr;
        padding-bottom: 1;
    }
    .message-user {
        background: #1e293b;
        border-left: solid #38bdf8;
        padding: 1;
        margin-bottom: 1;
    }
    .message-agent {
        background: #1e1e2e;
        border-left: solid #a855f7;
        padding: 1;
        margin-bottom: 1;
    }
    .message-author {
        margin-bottom: 1;
        text-style: bold;
    }
    #interactive-pane {
        background: #334155;
        border: solid #eab308;
        padding: 1;
        margin-bottom: 1;
    }
    #prompt-container {
        height: auto;
        border-top: solid #334155;
        padding-top: 1;
    }
    #chat-input {
        background: #1e293b;
        border: tall #38bdf8;
        color: #f8fafc;
    }
    Button {
        margin-top: 1;
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("r", "refresh_sessions", "Refresh"),
        ("ctrl+c", "quit", "Exit"),
        ("ctrl+q", "quit", "Exit"),
    ]

    def __init__(self, repo_root: Path | None = None) -> None:
        super().__init__()
        self.repo_root = repo_root or Path.cwd()
        self.session_mgr = SessionManager(repo_root=self.repo_root)
        self.active_ticket: TicketRunRecord | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("SESSIONS", id="sidebar-title")
                yield ListView(id="sessions-list")
                yield Button("Refresh", id="btn-refresh", variant="primary")
            with Vertical(id="main-chat"):
                with VerticalScroll(id="chat-scroll"):
                    yield ChatMessageWidget(
                        author="Agent",
                        content=(
                            "👋 Welcome to the **Azure DevOps SDLC Agent**!\n\n"
                            "You are in an active interactive coding session. Ask questions, "
                            "inspect code, or use slash commands:\n\n"
                            "- `/ado`: Inspect or verify Azure DevOps connection\n"
                            "- `/ado setup <org> <project> [repo]`: Update Azure DevOps settings\n"
                            "- `/run <ticket_id> [--dry-run]`: Run pipeline on a work item\n"
                            "- `/status`: View active ticket sessions and worktrees\n"
                            "- `/clean <ticket_id>`: Prune session and delete worktree\n"
                            "- `/help`: View all commands\n\n"
                            "_Type a question or command below and press Enter._"
                        ),
                        is_user=False,
                    )
                with Vertical(id="interactive-pane"):
                    pass
                with Vertical(id="prompt-container"):
                    yield Input(
                        placeholder="Type a coding query or slash command (/help, /ado)...",
                        id="chat-input",
                    )
        yield Footer()

    def on_mount(self) -> None:
        """Mount event: load active sessions and focus the chat input."""
        self.action_refresh_sessions()
        # Focus input bar immediately
        self.query_one("#chat-input", Input).focus()

    def action_refresh_sessions(self) -> None:
        """Fetch and populate tickets in the sidebar."""
        list_view = self.query_one("#sessions-list", ListView)
        list_view.clear()

        tickets = self.session_mgr.list_tickets()
        if not tickets:
            list_view.append(ListItem(Label("[dim]No sessions[/dim]")))
            return

        for t in tickets:
            list_view.append(TicketItem(t))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Inspect a ticket when clicked from the sidebar."""
        if isinstance(event.item, TicketItem):
            self.active_ticket = event.item.record
            self._render_ticket_pending_action(event.item.record)

    def _render_ticket_pending_action(self, record: TicketRunRecord) -> None:
        """Render interactive interrupt actions if ticket is waiting on human."""
        pane = self.query_one("#interactive-pane", Vertical)
        pane.remove_children()

        if record.status == SessionStatus.WAITING_ON_HUMAN and record.pending_request:
            req = record.pending_request
            rtype = req.request_type.upper()
            header = f"[bold yellow]⚠ TICKET #{record.ticket_id} ({rtype}):[/bold yellow]"
            pane.mount(Static(f"{header}\n{req.prompt}"))
            if req.options:
                for idx, opt in enumerate(req.options):
                    pane.mount(Label(f"Q{idx + 1}: {opt}"))
                    pane.mount(Input(placeholder="Your answer...", id=f"ans-input-{idx}"))
                pane.mount(Button("Submit Answers", id="btn-submit-answers", variant="success"))
        else:
            status_line = f"Status: {record.status.value} | Stage: {record.stage}"
            pane.mount(
                Static(
                    f"[bold cyan]Active Session:[/bold cyan] #{record.ticket_id} - {record.title}\n"
                    f"{status_line} | Branch: {record.branch_name}"
                )
            )

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user submitting text or slash commands."""
        text = event.value.strip()
        if not text:
            return

        inp = self.query_one("#chat-input", Input)
        inp.value = ""

        chat_scroll = self.query_one("#chat-scroll", VerticalScroll)

        # 1. Mount user message
        chat_scroll.mount(ChatMessageWidget(author="You", content=text, is_user=True))
        chat_scroll.scroll_end(animate=False)

        # 2. Check for exit
        if text.lower() in ("/exit", "/quit"):
            self.exit()
            return

        # 3. Handle slash command or normal chat
        if text.startswith("/"):
            response = self.session_mgr.execute_command(text)
            chat_scroll.mount(ChatMessageWidget(author="System", content=response, is_user=False))
            self.action_refresh_sessions()
        else:
            # Normal conversational agent chat
            response = self.session_mgr.chat(text)
            chat_scroll.mount(ChatMessageWidget(author="Agent", content=response, is_user=False))

        chat_scroll.scroll_end(animate=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "btn-refresh":
            self.action_refresh_sessions()
        elif event.button.id == "btn-submit-answers" and self.active_ticket:
            answers: dict[str, str] = {}
            if self.active_ticket.pending_request and self.active_ticket.pending_request.options:
                for idx, opt in enumerate(self.active_ticket.pending_request.options):
                    try:
                        inp_field = self.query_one(f"#ans-input-{idx}", Input)
                        answers[opt] = inp_field.value
                    except Exception:
                        pass

            resp = HumanResponse(
                session_id=f"ado-{self.active_ticket.ticket_id}",
                decision="answered",
                answers=answers,
            )
            self.session_mgr.submit_response(self.active_ticket.ticket_id, resp)
            self.notify(f"Submitted answers for ticket #{self.active_ticket.ticket_id}")

            chat_scroll = self.query_one("#chat-scroll", VerticalScroll)
            chat_scroll.mount(
                ChatMessageWidget(
                    author="System",
                    content=f"✔ Submitted answers for Ticket #{self.active_ticket.ticket_id}.",
                    is_user=False,
                )
            )
            pane = self.query_one("#interactive-pane", Vertical)
            pane.remove_children()
            self.action_refresh_sessions()


def run_tui(repo_root: Path | None = None) -> None:
    """Launch the interactive TUI application."""
    app = SDLCApp(repo_root=repo_root)
    app.run()
