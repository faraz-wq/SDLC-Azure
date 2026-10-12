# PROPOSED INTERACTIVE SCREENS & PROMPTS

Full terminal screen mockups for interactive conversational workflows.

---

## 1. Redesigned First-Contact & Welcome Screen (80x24 Standard Terminal)

```text
╭─ Azure DevOps SDLC Agent ────────────────────────────────────────────── [v0.1.0] ─╮
│ Work item in, verified draft pull request out.                                    │
│                                                                                   │
│ Target: /Users/faraz/Projects/SDLC-Azure (branch: main)                           │
│ Status: Azure DevOps [Connected: myorg/myproject] | OpenCode [Ready]              │
│                                                                                   │
│ Available Slash Commands:                                                         │
│   /run <id> [--dry-run]  Execute SDLC workflow on a work item                     │
│   /status                List in-flight ticket sessions and worktrees             │
│   /attach <id>           Inspect pending clarification questions or approvals     │
│   /clean <id>            Prune finished ticket session and delete worktree        │
│   /ado                   Inspect or update Azure DevOps configuration             │
│   /help                  Show command reference                                   │
│   /exit                  Quit interactive session                                 │
│                                                                                   │
│ Tip: Type a natural question to ask the assistant, or run `/run <id>` to begin.   │
╰───────────────────────────────────────────────────────────────────────────────────╯

sdlc-agent [main | myorg] > █
```

---

## 2. Redesigned Status Line / Context Toolbar

A pinned bottom line updating dynamically with repository and credentials context:

```text
sdlc-agent > /status
Active Sessions:
 • #42 [waiting_on_human] Fix database deadlock (Branch: agent/42-fix-deadlock)
   └─ Pending: plan_approval (Run `agent attach 42` to review)

────────────────────────────────────────────────────────────────────────────────────
 Repo: SDLC-Azure (main) │ ADO: Connected (myorg) │ Model: glm-5.3-flash │ /help
sdlc-agent [main] > █
```

---

## 3. Redesigned In-Session Permission & Consent Prompt (`/clean` & Dangerous Actions)

```text
sdlc-agent > /clean 42

╭─ Action Confirmation Required ───────────────────────────────────────────────────╮
│ Operation: DELETE Worktree & Session Tracking                                    │
│ Target:    Ticket #42 ("Fix database deadlock")                                  │
│ Paths:     .agent/worktrees/42/                                                  │
│ Database:  Record removed from .agent/sessions.sqlite                            │
│                                                                                   │
│ [WARN] This action is permanent and cannot be undone.                                  │
╰───────────────────────────────────────────────────────────────────────────────────╯
Are you sure you want to delete this session and worktree? [y/N]: █
```

---

## 4. Redesigned In-Session `/help` Screen

```text
sdlc-agent > /help

╭─ SDLC Agent Interactive Help ────────────────────────────────────────────────────╮
│ Workflow Commands:                                                               │
│   /run <id>             Start autonomous SDLC run on Azure DevOps work item      │
│   /run <id> --dry-run   Run locally without creating remote PRs or comments      │
│   /status               Show active sessions, worktree paths, and stage          │
│   /attach <id>          Inspect pending clarification questions or plan review   │
│   /clean <id>           Safely remove session state and delete local worktree    │
│                                                                                  │
│ Configuration & Environment:                                                     │
│   /ado                  Check organization, project, repo, and PAT token status  │
│   /ado setup <o> <p>    Configure Azure DevOps settings in .env                  │
│                                                                                  │
│ Session Controls:                                                                │
│   /clear                Clear current screen history                             │
│   /exit or /quit        Exit interactive assistant                               │
│                                                                                  │
│ Shortcuts:                                                                       │
│   Tab                   Autocomplete slash commands                              │
│   Ctrl+C                Clear current line (press twice to exit)                 │
│   Ctrl+D                Exit session                                             │
│   Up / Down             Recall command history                                   │
╰───────────────────────────────────────────────────────────────────────────────────╯

sdlc-agent [main] > █
```

---

## 5. Redesigned Interrupt & Cancel Hint Behavior

### Scenario A: Pressing `Ctrl+C` while typing
```text
sdlc-agent > how do I configure the worktree pat^C
(Input buffer cleared)
sdlc-agent > █
```

### Scenario B: Pressing `Ctrl+C` while agent is thinking / running
```text
sdlc-agent > /run 42
⠸ Running SDLC Agent pipeline on Ticket #42 (Stage: ingest)... ^C
Interrupt signal received. Cancelling in-flight task...
 Ingestion cancelled safely. State saved to checkpoint.
Run `/run 42` to resume from this step.

sdlc-agent [main] > █
```

