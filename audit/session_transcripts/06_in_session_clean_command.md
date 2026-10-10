# Session Transcript: In-Session Slash Command: /clean nonexistent and active tickets
**Session ID:** `06_in_session_clean_command`  
**Terminal Dimensions:** 120x40  
**Environment:** `TERM=xterm-256color`, sandbox=`/Users/faraz/Projects/SDLC-Azure/audit/sandbox/fakerepo`  
**Wall Clock Duration:** 3.92s  

---

## Scripted Keystrokes & Events
- **+1.2s**: `Clean ticket 42 via slash command` (Input: `/clean 42\n`)
- **+2.5s**: `Clean invalid ticket id` (Input: `/clean invalid_id\n`)
- **+3.8s**: `Exit session` (Input: `/exit\n`)

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
sdlc-agent > /clean 42
✔ Cleaned session and worktree for ticket #42.                                                                          

sdlc-agent > /clean invalid_id
Invalid ticket ID: invalid_id.                                                                                          

sdlc-agent > /exit
Goodbye!

```
