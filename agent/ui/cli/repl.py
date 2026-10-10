"""Interactive Terminal CLI REPL for Azure DevOps SDLC Agent.

Features:
- Clean inline terminal prompts
- Markdown formatted replies
- Slash commands (/ado, /run, /status, /help, /exit)
- Seamless coding agent assistance via Pi agent
"""

import sys
import termios
import tty
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from agent.session.manager import SessionManager

console = Console()

SLASH_COMMANDS: list[tuple[str, str]] = [
    ("/ado", "Inspect Azure DevOps connection & repo"),
    ("/ado setup <o> <p>", "Configure ADO organization, project, repo"),
    ("/run <id>", "Run full SDLC pipeline on a work item"),
    ("/run <id> --dry-run", "Run pipeline in safe local dry-run mode"),
    ("/status", "List active sessions and worktrees"),
    ("/clean <id>", "Prune ticket session and delete worktree"),
    ("/help", "Show command summary"),
    ("/exit", "Exit the application"),
]


def filter_commands(prefix: str) -> list[tuple[str, str]]:
    if not prefix.startswith("/"):
        return []
    p = prefix.lower()
    return [c for c in SLASH_COMMANDS if c[0].lower().startswith(p)]


def extract_completion(cmd_template: str) -> str:
    parts = cmd_template.split()
    if len(parts) > 1 and parts[1].startswith("<"):
        return parts[0] + " "
    return cmd_template


def read_interactive_line(prompt_text: str = "sdlc-agent > ") -> str:
    """Read a line interactively. If user types '/', popup commands with live count."""
    if not sys.stdin.isatty():
        return input(prompt_text).strip()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    buffer: list[str] = []
    cursor_pos = 0
    selected_idx = 0
    menu_rendered_lines = 0

    prompt_display = "\033[1;32msdlc-agent\033[0m \033[2m>\033[0m "
    prompt_len = len("sdlc-agent > ")
    max_menu_lines = len(SLASH_COMMANDS) + 1  # header + all commands

    # Pre-allocate buffer space below prompt to guarantee terminal never scrolls
    pre_alloc = f"\r\033[2K{prompt_display}" + "\n" * max_menu_lines + f"\033[{max_menu_lines}A"
    sys.stdout.write(pre_alloc)
    sys.stdout.flush()

    def clear_menu() -> None:
        nonlocal menu_rendered_lines
        if menu_rendered_lines > 0:
            for _ in range(menu_rendered_lines):
                sys.stdout.write("\n\033[2K")
            sys.stdout.write(f"\033[{menu_rendered_lines}A\r")
            menu_rendered_lines = 0

    def redraw_line_and_menu() -> None:
        nonlocal menu_rendered_lines, selected_idx
        clear_menu()

        # Render prompt + buffer
        line_str = "".join(buffer)
        sys.stdout.write(f"\r\033[2K{prompt_display}{line_str}")

        # Check if slash commands menu should be displayed
        matching = filter_commands(line_str)
        if matching:
            if selected_idx >= len(matching):
                selected_idx = len(matching) - 1
            if selected_idx < 0:
                selected_idx = 0

            total = len(matching)
            current_num = selected_idx + 1
            header = (
                f"\033[1;36mCommands [{current_num}/{total}]\033[0m "
                f"\033[2m(↑/↓ to navigate, Tab to complete, Enter to run, Esc to close):\033[0m"
            )
            menu_lines = [header]
            for i, (cmd, desc) in enumerate(matching):
                if i == selected_idx:
                    menu_lines.append(f"  \033[1;32m▶ {cmd:<22} {desc}\033[0m")
                else:
                    menu_lines.append(f"    \033[2m{cmd:<22}\033[0m {desc}")

            for m in menu_lines:
                sys.stdout.write(f"\n\033[2K\r{m}")
            menu_rendered_lines = len(menu_lines)

            # Move cursor back up to input line
            sys.stdout.write(f"\033[{menu_rendered_lines}A")

        # Reposition cursor on the input line
        target_col = prompt_len + cursor_pos + 1
        sys.stdout.write(f"\033[{target_col}G")
        sys.stdout.flush()

    try:
        tty.setraw(fd)
        redraw_line_and_menu()

        while True:
            ch = sys.stdin.read(1)

            if ch == "\x03":  # Ctrl+C
                clear_menu()
                sys.stdout.write("\n")
                sys.stdout.flush()
                raise KeyboardInterrupt

            if ch == "\x04":  # Ctrl+D
                if not buffer:
                    clear_menu()
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    raise EOFError
                continue

            if ch in ("\r", "\n"):  # Enter
                line_str = "".join(buffer)
                matching = filter_commands(line_str)
                clear_menu()
                sys.stdout.write("\n")
                sys.stdout.flush()

                if matching and line_str == "/":
                    # If user pressed enter on bare '/', execute or fill selected command
                    selected_cmd = matching[selected_idx][0]
                    return extract_completion(selected_cmd)
                return line_str.strip()

            if ch == "\t":  # Tab completion
                line_str = "".join(buffer)
                matching = filter_commands(line_str)
                if matching:
                    completed = extract_completion(matching[selected_idx][0])
                    buffer = list(completed)
                    cursor_pos = len(buffer)
                    selected_idx = 0
                    redraw_line_and_menu()
                continue

            if ch == "\x1b":  # Escape sequence
                seq1 = sys.stdin.read(1)
                if seq1 == "[":
                    seq2 = sys.stdin.read(1)
                    line_str = "".join(buffer)
                    matching = filter_commands(line_str)

                    if seq2 == "A":  # Up arrow
                        if matching:
                            selected_idx = (selected_idx - 1) % len(matching)
                            redraw_line_and_menu()
                        continue
                    elif seq2 == "B":  # Down arrow
                        if matching:
                            selected_idx = (selected_idx + 1) % len(matching)
                            redraw_line_and_menu()
                        continue
                    elif seq2 == "C":  # Right arrow
                        if cursor_pos < len(buffer):
                            cursor_pos += 1
                            redraw_line_and_menu()
                        continue
                    elif seq2 == "D":  # Left arrow
                        if cursor_pos > 0:
                            cursor_pos -= 1
                            redraw_line_and_menu()
                        continue
                elif seq1 in ("", "\x1b"):  # Standalone Escape
                    clear_menu()
                    buffer.clear()
                    cursor_pos = 0
                    redraw_line_and_menu()
                continue

            if ch in ("\x7f", "\x08"):  # Backspace
                if cursor_pos > 0:
                    buffer.pop(cursor_pos - 1)
                    cursor_pos -= 1
                    selected_idx = 0
                    redraw_line_and_menu()
                continue

            # Regular printable character
            if ch.isprintable():
                buffer.insert(cursor_pos, ch)
                cursor_pos += 1
                selected_idx = 0
                redraw_line_and_menu()

    finally:
        clear_menu()
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def run_interactive_cli(repo_root: Path | None = None) -> None:
    """Launch the interactive inline terminal CLI."""
    root = repo_root or Path.cwd()
    session_mgr = SessionManager(repo_root=root)

    welcome_text = (
        "[bold cyan]Azure DevOps SDLC Agent[/bold cyan]\n\n"
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
            user_input = read_interactive_line().strip()
        except KeyboardInterrupt:
            console.print("[dim]Input cleared. (Type /exit or press Ctrl+D to quit)[/dim]")
            continue
        except EOFError:
            console.print("[dim]Exiting SDLC Agent. Goodbye![/dim]")
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
