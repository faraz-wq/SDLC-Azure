"""Interactive Terminal CLI REPL for Azure DevOps SDLC Agent.

Styled like Claude Code / Antigravity CLI:
- Clean inline terminal prompts
- Markdown formatted replies
- Slash commands (/ado, /run, /status, /help, /exit)
- Seamless coding agent assistance via Pi agent
"""

from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from agent.session.manager import SessionManager

console = Console()


def run_interactive_cli(repo_root: Path | None = None) -> None:
    """Launch the interactive inline terminal CLI (Claude Code / Antigravity style)."""
    root = repo_root or Path.cwd()
    session_mgr = SessionManager(repo_root=root)

    welcome_text = (
        "[bold cyan]Azure DevOps SDLC Agent[/bold cyan] (Claude Code / Antigravity style)\n\n"
        "Ask coding questions, inspect repo, or use slash commands:\n"
        "  [bold cyan]/ado[/bold cyan]               Inspect Azure DevOps connection & repo\n"
        "  [bold cyan]/ado setup <o> <p>[/bold cyan] Configure ADO organization, project, repo\n"
        "  [bold cyan]/run <id>[/bold cyan]          Run full SDLC pipeline on a work item\n"
        "  [bold cyan]/run <id> --dry-run[/bold cyan] Run pipeline in safe local dry-run mode\n"
        "  [bold cyan]/status[/bold cyan]            List active sessions and worktrees\n"
        "  [bold cyan]/clean <id>[/bold cyan]        Prune ticket session and delete worktree\n"
        "  [bold cyan]/help[/bold cyan]              Show command summary\n"
        "  [bold cyan]/exit[/bold cyan] or [bold cyan]/quit[/bold cyan]    Exit\n"
    )

    console.print(Panel(welcome_text, border_style="cyan", title="Interactive SDLC Terminal"))

    while True:
        try:
            user_input = console.input("[bold green]sdlc-agent[/bold green] [dim]>[/dim] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Exiting SDLC Agent. Goodbye![/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
            console.print("[dim]Goodbye![/dim]")
            break

        if user_input.startswith("/"):
            # Slash command
            response = session_mgr.execute_command(user_input)
            console.print(Markdown(response))
            console.print()
        else:
            # Natural coding assistant query via Pi agent
            with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                response = session_mgr.chat(user_input)
            console.print(Markdown(response))
            console.print()

