# Session Transcript: Signal Handling: Ctrl+C, Ctrl+D, EOF at Idle Prompt
**Session ID:** `04_interruption_signals`  
**Terminal Dimensions:** 120x40  
**Environment:** `TERM=xterm-256color`, sandbox=`/Users/faraz/Projects/SDLC-Azure/audit/sandbox/fakerepo`  
**Wall Clock Duration:** 1.64s  

---

## Scripted Keystrokes & Events
- **+1.5s**: `Send SIGINT (Ctrl+C) at idle prompt` (Input: `b'\x03'`)
- **+3.0s**: `Send EOF (Ctrl+D) at idle prompt` (Input: `b'\x04'`)

---

## Complete Rendered Output (Plain Text Screen Capture)

```text
╭───────────────────────────────────────────── Interactive SDLC Terminal ──────────────────────────────────────────────╮
│ Azure DevOps SDLC Agent (Claude Code / Antigravity style)                                                            │
│                                                                                                                      │
│ Ask coding questions, inspect repo, or use slash commands:                                                           │
│   /ado               Inspect Azure DevOps connection & repo                                                          │
│   /ado setup <o> <p> Configure ADO organization, project, repo                                                       │
│   /run <id>          Run full SDLC pipeline on a work item                                                           │
│   /run <id> --dry-run Run pipeline in safe local dry-run mode                                                        │
│   /status            List active sessions and worktrees                                                              │
│   /clean <id>        Prune ticket session and delete worktree                                                        │
│   /help              Show command summary                                                                            │
│   /exit or /quit    Exit                                                                                             │
│                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
sdlc-agent > ^C
Exiting SDLC Agent. Goodbye!

```
