# Azure DevOps SDLC Agent (`agent`)

An autonomous software development lifecycle agent built with LangGraph: **work item in, verified draft pull request out**.

The agent automates work item ingestion, clarification scoring, blast-radius impact analysis, test-driven code implementation, sandboxed verification, and draft PR generation with human-in-the-loop approval interrupts.

---

## Installation & Prerequisites

### Prerequisites
- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager
- Git

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/example/ado-sdlc-agent.git
cd ado-sdlc-agent

# Install dependencies in virtual environment
uv sync

# Run the CLI entrypoint
uv run agent --help
```

---

## Quick Start (Verified Commands)

### 1. Configure Azure DevOps Connection
Create a `.env` file in the project root:

```env
AZURE_DEVOPS_ORG=your-org-name
AZURE_DEVOPS_PROJECT=your-project-name
AZURE_DEVOPS_REPO=your-repo-name
AZURE_DEVOPS_PAT=your-azure-devops-personal-access-token
OPENCODE_API_KEY=your-opencode-api-key
```

### 2. Initialize a Repository Workspace

```bash
uv run agent init
```
*Creates the local `.agent/` tracking directory, SQLite session database, and worktree cache.*

### 3. Run Pipeline on a Work Item (Safe Dry-Run Mode)

```bash
uv run agent run 42 --dry-run
```
*Executes the pipeline locally inside an isolated worktree on branch `agent/42-...`. In dry-run mode, zero writes or comments are made to Azure DevOps.*

### 4. Check Status of In-Flight Tickets

```bash
uv run agent status
```

**Output:**
```text
                   Azure DevOps SDLC Agent - Active Sessions                    
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Ticket ID ┃ Title         ┃ Branch        ┃ Status  ┃ Stage  ┃ Pending       ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━┩
│        42 │ Fix deadlock  │ agent/42-fix  │ waiting │ plan   │ plan_approval │
└───────────┴───────────────┴───────────────┴─────────┴────────┴───────────────┘
```

### 5. Inspect Pending Human Approvals

```bash
uv run agent attach 42
```

### 6. Clean Up a Finished Ticket and Worktree

```bash
uv run agent clean 42
```

---

## Interactive Interfaces

### Terminal Chat (Claude Code / Antigravity Style)

Launch the inline conversational terminal assistant:
```bash
uv run agent chat
```
*Supports natural coding queries alongside slash commands (`/ado`, `/run 42`, `/status`, `/clean 42`, `/help`, `/exit`).*

### Full-Screen Terminal UI (TUI)

Launch the interactive Textual dashboard:
```bash
uv run agent tui
```
*Provides dual-pane browsing of active ticket sessions, diff previews, and clarification forms.*

---

## Command Reference

| Command | Arguments | Options | Description |
|---|---|---|---|
| `run` | `<ticket_id>` | `--dry-run`, `--repo <path>` | Run SDLC agent pipeline on a work item |
| `status` | — | `--repo <path>` | List all active sessions and worktrees |
| `list` | — | `--repo <path>` | Alias for `status` |
| `attach` | `<ticket_id>` | `--repo <path>` | Inspect session details and pending approvals |
| `clean` | `<ticket_id>` | `--repo <path>` | Delete session record and isolated worktree |
| `init` | — | `--repo <path>` | Initialize `.agent` tracking workspace |
| `chat` | — | `--repo <path>` | Start interactive terminal REPL |
| `tui` | — | `--repo <path>` | Start full-screen Textual dashboard |

---

## Exit Codes

- `0`: Success
- `1`: Domain or runtime failure (ticket not found, network error)
- `2`: Invalid CLI syntax or unknown option

