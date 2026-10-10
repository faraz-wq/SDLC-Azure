# CLI CONVENTIONS & ARCHITECTURAL STANDARDS: `agent`

This document defines tool-wide standards for streams, exit codes, output formatting, flags, and configuration.

---

## 1. Exit Code Matrix

| Code | Meaning | Example Trigger |
|---|---|---|
| **0** | **Success** | Pipeline completed, table listed, ticket cleaned |
| **1** | **Runtime Domain Failure** | Ticket not found, connection failure, guardrail violation |
| **2** | **Usage / CLI Syntax Error** | Invalid flag, missing required argument, non-integer ticket ID |
| **130** | **Interrupted (SIGINT)** | User cancelled execution via `Ctrl+C` |

---

## 2. Standard Streams (Stdout vs. Stderr)

- **STDOUT:** Reserved strictly for successful command payload data:
  - Rich tables (`agent status`)
  - Machine-readable JSON (`--json`)
  - Confirmation status messages (`✔ Initialized...`)
- **STDERR:** Reserved exclusively for:
  - Error boxes and diagnostic messages
  - Interactive spinner / progress animations
  - Debug logs (`--verbose`)

**Rule:** `agent status | head -n 1` must not crash with Python `BrokenPipeError`.

---

## 3. Flag & Option Standards

1. **Short & Long Option Parity:**
   - `--help` $\rightarrow$ `-h`
   - `--version` $\rightarrow$ `-v`
   - `--repo` $\rightarrow$ `-r`
   - `--dry-run` $\rightarrow$ `-d`
   - `--yes` $\rightarrow$ `-y`
2. **Flag Flexibility:** Both `--repo=/path` and `--repo /path` must function identically.
3. **Double Dash:** `--` must terminate flag parsing and treat subsequent tokens as positional arguments.

---

## 4. Machine-Readable Output (`--json`) Policy

- When `--json` is specified:
  - **Zero ANSI escape sequences** or terminal color codes are emitted.
  - Output must parse cleanly with `jq .` with zero non-JSON prefix or suffix lines.
  - If a command fails and `--json` was requested, the error output on STDERR must also be emitted as structured JSON:
    ```json
    {
      "error": {
        "code": "ado_connection_failed",
        "message": "Failed to fetch work item #42",
        "details": "HTTP 404 Not Found"
      }
    }
    ```

---

## 5. Color & Terminal Detection Policy

- Honors the [NO_COLOR](https://no-color.org/) standard: if `NO_COLOR` is present in the environment (any non-empty value), all colored text, styles, and ANSI codes are omitted.
- Respects `TERM=dumb`: spinners and interactive updating panels fall back to plain log lines.
- TTY Detection: If running non-interactively (`sys.stdin.isatty() == False`), interactive prompts (`[y/N]`) abort unless `--yes` is passed.

---

## 6. Configuration Precedence Order

When resolving parameters (e.g. ADO credentials, repository root), the tool must resolve in this strict order:
1. **Explicit CLI flags** (`--repo`, `--dry-run`)
2. **Environment variables** (`AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PAT`, `PROJECT_ROOT`)
3. **Project config file** (`.env` in current directory or `--repo`)
4. **Hardcoded defaults** (`dry_run=False`, `project_root=Path.cwd()`)

