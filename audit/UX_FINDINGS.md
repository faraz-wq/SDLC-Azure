# INTERACTIVE & CONVERSATIONAL UX FINDINGS (`agent chat` & `agent tui`)

All findings are backed by reproducible sessions in `./audit/session_transcripts/`.

---

## 1. Critical Severity Findings

```
ID: INT-F001
Title: In-session destructive slash command `/clean` executes with zero confirmation
Severity: Critical
Confidence: Verified
Category: Permissions & Safety
Location: agent/ui/cli/repl.py:53, agent/session/manager.py:83
Evidence:
  Transcript: 06_in_session_clean_command.md
  User types: `/clean 42`
  Output:
     Cleaned session and worktree for ticket #42.
  Behavior: Deletes directory .agent/worktrees/42 and removes database row immediately.
Reproduction:
  1. Launch `uv run python -m agent.ui.cli.main chat`
  2. Type `/clean 42` (or any ticket ID)
  3. Notice it destroys files on disk without asking "Are you sure? [y/N]"
Impact: A typo in a ticket ID or accidental paste can permanently destroy a developer's
  work-in-progress git worktree and branch state with zero opportunity to abort.
Root cause: `SessionManager.execute_command` directly invokes `self.clean_ticket(t_id)`
  without any confirmation gate.
Recommendation (S):
  Add an interactive prompt in `repl.py`:
  `Confirm deletion of worktree and session for Ticket #42? [y/N]`
  Require explicit confirmation before proceeding.
```

---

## 2. High Severity Findings

```
ID: INT-F002
Title: Pressing `Ctrl+C` at an idle prompt immediately kills the application
Severity: High
Confidence: Verified
Category: Control & Interruption
Location: agent/ui/cli/repl.py:40-44
Evidence:
  Transcript: 04_interruption_signals.md
  User presses: Ctrl+C at `sdlc-agent > ` prompt
  Output:
    ^C
    Exiting SDLC Agent. Goodbye!
  Exit code: Process exits to OS shell.
Reproduction:
  1. Launch `uv run python -m agent.ui.cli.main chat`
  2. At the prompt, press `Ctrl+C` to cancel a typed thought or clear the line.
  3. Tool abruptly terminates.
Impact: Severe violation of terminal CLI UX conventions. In bash, zsh, Claude Code,
  and aider, Ctrl+C clears the current input line. An accidental Ctrl+C discards the entire
  session instead of clearing the prompt.
Root cause: `repl.py` catches `(KeyboardInterrupt, EOFError)` and executes `break` immediately.
Recommendation (S):
  Separate `KeyboardInterrupt` from `EOFError`. On `KeyboardInterrupt`, print `^C`,
  clear the current buffer, and continue the loop. Only exit if pressed twice in rapid
  succession (within 1 second) or if `Ctrl+D` (EOFError) is received.
```

```
ID: INT-F003
Title: Complete absence of a persistent status line / context footer
Severity: High
Confidence: Verified
Category: Status & Feedback
Location: agent/ui/cli/repl.py:38
Evidence:
  Transcripts: 01_first_contact.md, 02_slash_commands_and_typos.md
  Screen render:
    sdlc-agent >
  Information missing:
    - Current repository / working directory
    - Active git branch
    - Active model / inference provider status
    - Azure DevOps connection status (authenticated / unauthenticated)
    - Token budget / context limit
Reproduction:
  1. Observe terminal screen during an interactive session.
  2. Notice the user has no persistent feedback on system state.
Impact: Users operate "blind." They do not know if their PAT token is active, which repo
  is targeted, or if they are in dry-run mode until an operation fails.
Root cause: Uses a bare `console.input()` without prompt-toolkit or Rich Live footer bar.
Recommendation (M):
  Adopt a persistent bottom toolbar (via `prompt_toolkit` or Rich panel) showing:
  `[repo: myrepo | branch: main | ADO: connected | Model: glm-5.3-flash | /help]`
```

```
ID: INT-F004
Title: Standard `console.input()` does not support multiline input or bracketed paste
Severity: High
Confidence: Verified
Category: Input Experience
Location: agent/ui/cli/repl.py:40
Evidence:
  Transcript: 03_input_stress_and_edge_cases.md
  Behavior:
    - Pressing Enter always executes; no Shift+Enter or `\`+Enter multiline escape.
    - Pasting a block of code with embedded newlines fires multiple queries sequentially.
Impact: Developers cannot paste code snippets, error tracebacks, or detailed acceptance
  criteria into the chat interface without accidental premature execution.
Root cause: Standard Python `input()` / Rich `console.input()` reads line-by-line from stdin.
Recommendation (M):
  Migrate from `console.input()` to `prompt_toolkit.PromptSession` with multiline support
  (e.g. `Alt+Enter` for newline) and bracketed paste protection enabled.
```

---

## 3. Medium Severity Findings

```
ID: INT-F005
Title: Slash command typos lack fuzzy suggestions and dead-end the user
Severity: Medium
Confidence: Verified
Category: Error Quality & Recovery
Location: agent/session/manager.py:149
Evidence:
  Transcript: 02_slash_commands_and_typos.md
  User types: `/hepl`
  Output:
    Unknown command: `/hepl`. Type `/help` for available commands.
Reproduction:
  1. Type `/hepl`, `/stat`, or `/ad` in the chat prompt.
Impact: Slows down workflow; fails modern CLI expectations (like git or typer which suggest
  "Did you mean 'status'?").
Root cause: Simple `if/elif/else` dispatch with a static fallback string.
Recommendation (S):
  Use `difflib.get_close_matches(cmd, valid_commands)`:
  "Unknown command `/hepl`. Did you mean `/help`?"
```

```
ID: INT-F006
Title: Natural language queries output raw HTTP 401 strings on unconfigured environments
Severity: Medium
Confidence: Verified
Category: Polish & Trust
Location: agent/session/manager.py:73-77
Evidence:
  Transcript: 05_natural_query_agent_chat.md
  User types: `Can you review the files in this repository?`
  Output:
    ⠋ Thinking... (2s)
    Error communicating with AI assistant: HTTP Error 401: Unauthorized
Reproduction:
  1. In an unconfigured environment, ask any conversational question.
Impact: User is given an unhelpful HTTP error code without actionable next steps.
Root cause: `SessionManager.chat()` catches generic Exception and returns `f"Error communicating with AI assistant: {e}"`.
Recommendation (S):
  Detect 401 / authentication errors and format a clear guidance message:
  "Authentication error: OPENCODE_API_KEY is missing or invalid. Check your .env file."
```

```
ID: INT-F007
Title: Small terminal (40x15) squashes welcome panel into an awkward vertical strip
Severity: Medium
Confidence: Verified
Category: Accessibility & Robustness
Location: agent/ui/cli/repl.py:34
Evidence:
  Transcript: 07_small_terminal_and_no_color.md
  In 40x15 terminal, the welcome box takes up 14 of 15 vertical lines, pushing the prompt
  to the very bottom edge and wrapping commands awkwardly across multiple lines.
Root cause: Fixed multi-line welcome banner rendered unconditionally on startup.
Recommendation (S):
  Inspect terminal width (`console.size.width`); if `< 60`, render a compact 2-line header:
  `SDLC Agent (40 cols) | Type /help for commands, /exit to quit.`
```

---

## 4. Unverified Suspicions

1. **Terminal Scrollback Desynchronization during Textual TUI resize:** In `agent tui`, resizing the terminal while long diffs are rendered in the sidebar may cause Textual to leak scroll offsets or drop focus from the input bar.
2. **Zombie Pi Subprocesses on Mid-Task Exit:** If a user closes the terminal window (sending `SIGHUP`) while Pi coding agent is running a background compilation, the child process might not be terminated cleanly.
