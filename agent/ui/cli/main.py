"""CLI interface for Azure DevOps SDLC agent.

Rule: UI code talks only to agent/session/. It never imports nodes, adapters, or connectors.
"""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from agent.session.manager import SessionManager
from agent.session.models import SessionStatus

app = typer.Typer(
    help="Azure DevOps SDLC Agent CLI",
    invoke_without_command=True,
)
console = Console()


@app.callback()
def main_callback(ctx: typer.Context) -> None:
    """Default entrypoint: launch interactive TUI if no subcommand given."""
    if ctx.invoked_subcommand is None:
        from agent.ui.tui.app import run_tui

        run_tui()


@app.command("tui")
def tui_cmd(
    repo: Annotated[str | None, typer.Option("--repo", help="Path to repository root")] = None,
) -> None:
    """Launch the interactive OpenCode-style Terminal UI."""
    from agent.ui.tui.app import run_tui

    repo_path = Path(repo) if repo else Path.cwd()
    run_tui(repo_root=repo_path)


@app.command("init")
def init_cmd(
    repo: Annotated[str | None, typer.Option("--repo", help="Path to repository root")] = None,
) -> None:
    """Initialize .agent workspace in the target repository."""
    repo_path = Path(repo) if repo else Path.cwd()
    sm = SessionManager(repo_root=repo_path)
    ctx = sm.init_project()
    console.print(f"[green]✔ Initialized agent workspace at:[/green] {ctx.dot_agent_dir}")


@app.command("status")
@app.command("list")
def status_cmd(
    repo: Annotated[str | None, typer.Option("--repo", help="Path to repository root")] = None,
) -> None:
    """List all tracked ticket sessions, feature branches, and statuses."""
    repo_path = Path(repo) if repo else Path.cwd()
    sm = SessionManager(repo_root=repo_path)
    tickets = sm.list_tickets()

    if not tickets:
        console.print("[dim]No active ticket sessions found in workspace.[/dim]")
        return

    table = Table(title="Azure DevOps SDLC Agent - Active Sessions")
    table.add_column("Ticket ID", style="cyan", justify="right")
    table.add_column("Title", style="white")
    table.add_column("Branch", style="magenta")
    table.add_column("Status", style="bold")
    table.add_column("Stage", style="blue")
    table.add_column("Pending Action", style="yellow")

    for t in tickets:
        status_color = "green" if t.status == SessionStatus.DONE else "yellow"
        if t.status == SessionStatus.WAITING_ON_HUMAN:
            status_color = "bold red"

        pending_desc = f"{t.pending_request.request_type}" if t.pending_request else "None"
        table.add_row(
            str(t.ticket_id),
            t.title,
            t.branch_name,
            f"[{status_color}]{t.status.value}[/{status_color}]",
            t.stage,
            pending_desc,
        )

    console.print(table)


@app.command("attach")
def attach_cmd(
    ticket_id: Annotated[int, typer.Argument(help="ID of the work item to inspect")],
    repo: Annotated[str | None, typer.Option("--repo", help="Path to repository root")] = None,
) -> None:
    """Attach to and inspect an in-flight or waiting ticket session."""
    repo_path = Path(repo) if repo else Path.cwd()
    sm = SessionManager(repo_root=repo_path)
    run = sm.project.get_ticket_run(ticket_id)

    if not run:
        console.print(f"[red]Error:[/red] No session found for ticket #{ticket_id}")
        raise typer.Exit(code=1)

    console.print(f"[bold cyan]Ticket #{run.ticket_id}:[/bold cyan] {run.title}")
    console.print(f"[dim]Branch:[/dim] {run.branch_name}")
    console.print(f"[dim]Worktree:[/dim] {run.worktree_path}")
    console.print(f"[dim]Status:[/dim] {run.status.value} (Stage: {run.stage})")

    if run.pending_request:
        console.print("\n[bold yellow]Pending Human Action Required:[/bold yellow]")
        console.print(f"Type: {run.pending_request.request_type}")
        console.print(f"Prompt: {run.pending_request.prompt}")
        if run.pending_request.options:
            console.print("Options:")
            for opt in run.pending_request.options:
                console.print(f" - {opt}")


@app.command("clean")
def clean_cmd(
    ticket_id: Annotated[int, typer.Argument(help="ID of the ticket session to clean")],
    repo: Annotated[str | None, typer.Option("--repo", help="Path to repository root")] = None,
) -> None:
    """Clean up and remove a ticket session and its local worktree."""
    repo_path = Path(repo) if repo else Path.cwd()
    sm = SessionManager(repo_root=repo_path)
    sm.clean_ticket(ticket_id, remove_worktree=True)
    console.print(f"[green]✔ Cleaned session and worktree for ticket #{ticket_id}[/green]")


if __name__ == "__main__":
    app()
