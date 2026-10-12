"""CLI interface for Azure DevOps SDLC agent.

Rule: UI code talks only to agent/session/. It never imports nodes, adapters, or connectors.
"""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent.session.manager import SessionManager
from agent.session.models import SessionStatus

app = typer.Typer(
    help="Azure DevOps SDLC Agent CLI",
    invoke_without_command=True,
)
console = Console()
err_console = Console(stderr=True)


def version_callback(value: bool) -> None:
    if value:
        console.print("ado-sdlc-agent version 0.1.0")
        raise typer.Exit(code=0)


@app.callback()
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show program version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Default entrypoint: launch interactive CLI REPL if no subcommand given."""
    if ctx.invoked_subcommand is None:
        from agent.ui.cli.repl import run_interactive_cli

        run_interactive_cli()


@app.command("chat")
def chat_cmd(
    repo: Annotated[str | None, typer.Option("--repo", help="Path to repository root")] = None,
) -> None:
    """Launch the interactive terminal CLI."""
    from agent.ui.cli.repl import run_interactive_cli

    repo_path = Path(repo) if repo else Path.cwd()
    run_interactive_cli(repo_root=repo_path)


@app.command("tui")
def tui_cmd(
    repo: Annotated[str | None, typer.Option("--repo", help="Path to repository root")] = None,
) -> None:
    """Launch the alternative full-screen Textual TUI."""
    from agent.ui.tui.app import run_tui

    repo_path = Path(repo) if repo else Path.cwd()
    run_tui(repo_root=repo_path)


@app.command("run")
def run_cmd(
    ticket_id: Annotated[int, typer.Argument(help="ID of the work item to execute")],
    dry_run: Annotated[
        bool, typer.Option("--dry-run", "-d", help="Simulate without remote writes")
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output run result as JSON")] = False,
    repo: Annotated[str | None, typer.Option("--repo", help="Path to repository root")] = None,
) -> None:
    """Run the SDLC agent on a work item."""
    repo_path = Path(repo) if repo else Path.cwd()
    sm = SessionManager(repo_root=repo_path)
    if not json_output:
        console.print(f"[bold cyan]Starting SDLC Agent for Ticket #{ticket_id}...[/bold cyan]")
    try:
        run = sm.run_ticket(ticket_id, dry_run=dry_run)
    except Exception as e:
        if json_output:
            import json

            print(json.dumps({"error": str(e), "ticket_id": ticket_id}))
            raise typer.Exit(code=1) from None
        err_console.print(
            Panel(
                f"[bold red]What:[/bold red] Could not complete SDLC run for Ticket #{ticket_id}\n"
                f"[bold yellow]Why:[/bold yellow]  {e}\n\n"
                f"[bold cyan]Next:[/bold cyan] Check Azure DevOps credentials in `.env` "
                f"or run `/ado setup` in `agent chat`.",
                title="Azure DevOps Run Error",
                border_style="red",
            )
        )
        raise typer.Exit(code=1) from None

    if json_output:
        print(run.model_dump_json(indent=2))
        return

    console.print(f"[bold]Status:[/bold] {run.status.value} (Stage: {run.stage})")

    if run.pending_request:
        req_type = run.pending_request.request_type
        console.print(f"\n[bold yellow]Paused on Human Input ({req_type}):[/bold yellow]")
        console.print(run.pending_request.prompt)
    elif run.pr_url:
        console.print(f"\n[bold green]Draft PR Created:[/bold green] {run.pr_url}")


@app.command("init")
def init_cmd(
    repo: Annotated[str | None, typer.Option("--repo", help="Path to repository root")] = None,
) -> None:
    """Initialize .agent workspace in the target repository."""
    repo_path = Path(repo) if repo else Path.cwd()
    sm = SessionManager(repo_root=repo_path)
    ctx = sm.init_project()
    console.print(f"[green]Initialized agent workspace at:[/green] {ctx.dot_agent_dir}")


@app.command("status")
@app.command("list")
def status_cmd(
    json_output: Annotated[bool, typer.Option("--json", help="Output sessions as JSON")] = False,
    repo: Annotated[str | None, typer.Option("--repo", help="Path to repository root")] = None,
) -> None:
    """List all tracked ticket sessions, feature branches, and statuses."""
    repo_path = Path(repo) if repo else Path.cwd()
    sm = SessionManager(repo_root=repo_path)
    tickets = sm.list_tickets()

    if json_output:
        import json

        data = [t.model_dump() for t in tickets]
        print(json.dumps(data, default=str, indent=2))
        return

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
    json_output: Annotated[bool, typer.Option("--json", help="Output session as JSON")] = False,
    repo: Annotated[str | None, typer.Option("--repo", help="Path to repository root")] = None,
) -> None:
    """Attach to and inspect an in-flight or waiting ticket session."""
    repo_path = Path(repo) if repo else Path.cwd()
    sm = SessionManager(repo_root=repo_path)
    run = sm.project.get_ticket_run(ticket_id)

    if not run:
        err_console.print(f"[red]Error:[/red] No session found for ticket #{ticket_id}")
        raise typer.Exit(code=1)

    if json_output:
        print(run.model_dump_json(indent=2))
        return

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
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
    repo: Annotated[str | None, typer.Option("--repo", help="Path to repository root")] = None,
) -> None:
    """Clean up and remove a ticket session and its local worktree."""
    repo_path = Path(repo) if repo else Path.cwd()
    sm = SessionManager(repo_root=repo_path)
    run = sm.project.get_ticket_run(ticket_id)
    if not run:
        err_console = Console(stderr=True)
        err_console.print(f"[red]Error:[/red] Ticket session #{ticket_id} does not exist.")
        raise typer.Exit(code=1)

    if not yes:
        confirm = typer.confirm(
            f"Are you sure you want to delete session and worktree for Ticket #{ticket_id}?"
        )
        if not confirm:
            console.print("[dim]Aborted.[/dim]")
            raise typer.Exit(code=0)

    sm.clean_ticket(ticket_id, remove_worktree=True)
    console.print(f"[green]Cleaned session and worktree for ticket #{ticket_id}[/green]")


if __name__ == "__main__":
    app()
