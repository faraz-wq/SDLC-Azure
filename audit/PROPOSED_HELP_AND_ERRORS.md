# PROPOSED HELP & ERROR SCREENS

## 1. Redesigned Top-Level Help (`agent --help`)

```text
Usage: agent [OPTIONS] COMMAND [ARGS]...

  Azure DevOps SDLC Agent CLI.
  Work item in, tested draft pull request out.

Options:
  -v, --version         Show program version and exit.
  -h, --help            Show this message and exit.
  --install-completion  Install shell completion.
  --show-completion     Show completion script.

Commands:
  run     Run the SDLC agent workflow on a work item.
  status  Display active ticket sessions and branch statuses. (alias: list)
  attach  Inspect pending human approvals or questions for a ticket.
  clean   Remove local worktree and session data for a ticket.
  ado     Inspect or configure Azure DevOps connection.
  chat    Launch interactive terminal assistant (Claude Code / Antigravity style).
  tui     Launch interactive full-screen terminal UI.
  init    Initialize .agent workspace directory in the repository.

Examples:
  $ agent ado setup myorg myproject myrepo
  $ agent run 42 --dry-run
  $ agent status
  $ agent attach 42
  $ agent clean 42 --yes
```

---

## 2. Redesigned `agent run --help`

```text
Usage: agent run [OPTIONS] TICKET_ID

  Run the SDLC agent workflow on a work item.

Arguments:
  TICKET_ID             Integer ID of the Azure DevOps work item. [required]

Options:
  -d, --dry-run         Simulate pipeline without remote writes or PR creation.
  -r, --repo PATH       Target repository root. [default: current directory]
  --json                Output run metrics and result as JSON.
  -h, --help            Show this message and exit.

Examples:
  $ agent run 42
  $ agent run 42 --dry-run
  $ agent run 42 --json | jq .outcome
```

---

## 3. Redesigned `agent clean --help`

```text
Usage: agent clean [OPTIONS] TICKET_ID

  Remove local worktree and session data for a ticket.

Arguments:
  TICKET_ID             Integer ID of the ticket session to delete. [required]

Options:
  -y, --yes             Skip interactive confirmation prompt.
  -r, --repo PATH       Target repository root. [default: current directory]
  -h, --help            Show this message and exit.

Examples:
  $ agent clean 42
  $ agent clean 42 --yes
```

---

## 4. Standard Error Format Template

All command-line errors must conform to the 4-part structure rendered to **STDERR**:

```
╭─ [Error Category] ───────────────────────────────────────────────────────────╮
│ What:  <Concise sentence describing what operation failed>                   │
│ Where: <Argument, flag, file, or remote endpoint involved>                   │
│ Why:   <Underlying root cause, error code, or missing prerequisite>          │
│                                                                              │
│ Next:  <Specific, actionable command or remediation step>                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## 5. Rewritten Top 5 Error Messages

### Error 1: Missing or Invalid Azure DevOps Credentials
- **Old:** 120-line `urllib.error.HTTPError: HTTP Error 404: Not Found` traceback.
- **Rewritten:**
  ```text
  ╭─ Azure DevOps Connection Error ──────────────────────────────────────────────╮
  │ What:  Failed to fetch work item #42 from Azure DevOps.                      │
  │ Where: https://dev.azure.com/myorg/myproject/_apis/wit/workitems/42         │
  │ Why:   Received HTTP 404. Organization, project, or ticket does not exist.   │
  │                                                                              │
  │ Next:  Verify your settings with `agent ado` or configure credentials in     │
  │        .env using `agent ado setup <org> <project> [repo]`.                  │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ```

### Error 2: Session Not Found (`agent attach <id>`)
- **Old:** `Error: No session found for ticket #9999` (on STDOUT, exit 1).
- **Rewritten:**
  ```text
  ╭─ Session Not Found ──────────────────────────────────────────────────────────╮
  │ What:  No active session found for ticket #9999.                             │
  │ Where: .agent/sessions.sqlite                                                │
  │ Why:   Ticket #9999 has not been run in this workspace.                      │
  │                                                                              │
  │ Next:  Run `agent status` to view active sessions, or start work with        │
  │        `agent run 9999`.                                                     │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ```

### Error 3: Deletion of Nonexistent Ticket (`agent clean <id>`)
- **Old:** ` Cleaned session and worktree for ticket #9999` (false positive).
- **Rewritten:**
  ```text
  ╭─ Cannot Clean Ticket ────────────────────────────────────────────────────────╮
  │ What:  Could not remove ticket #9999.                                        │
  │ Where: .agent/sessions.sqlite and .agent/worktrees/9999                      │
  │ Why:   Ticket session does not exist.                                        │
  │                                                                              │
  │ Next:  Run `agent status` to verify ticket IDs currently in flight.          │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ```

### Error 4: Invalid Argument Type
- **Old:** Typer default `Invalid value for 'TICKET_ID': 'abc' is not a valid integer.`
- **Rewritten:**
  ```text
  ╭─ Invalid Argument ───────────────────────────────────────────────────────────╮
  │ What:  Invalid ticket ID 'abc'.                                              │
  │ Where: Argument <TICKET_ID>                                                  │
  │ Why:   Azure DevOps ticket IDs must be positive integers.                    │
  │                                                                              │
  │ Next:  Provide an integer ID, e.g. `agent run 101`.                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ```

### Error 5: Scope Guard Violation (During verification)
- **Old:** Python exception `ScopeViolationError: File 'src/evil.cs' is outside the approved plan allowed_files`
- **Rewritten:**
  ```text
  ╭─ Guardrail Violation: Scope Guard ───────────────────────────────────────────╮
  │ What:  Coding agent attempted to modify files outside the approved plan.     │
  │ Where: File: src/evil.cs (Plan allowed: ['src/Core/**', 'tests/**'])         │
  │ Why:   Safety policy strictly prohibits touching undeclared files.           │
  │                                                                              │
  │ Next:  Run `agent attach <id>` to inspect or modify the approved plan.       │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ```

