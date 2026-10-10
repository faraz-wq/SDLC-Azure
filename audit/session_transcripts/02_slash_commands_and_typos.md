# Session Transcript: Slash Commands Discovery, Typos and Unknown Commands
**Session ID:** `02_slash_commands_and_typos`  
**Terminal Dimensions:** 120x40  
**Environment:** `TERM=xterm-256color`, sandbox=`/Users/faraz/Projects/SDLC-Azure/audit/sandbox/fakerepo`  
**Wall Clock Duration:** 6.33s  

---

## Scripted Keystrokes & Events
- **+1.2s**: `Check active sessions status` (Input: `/status\n`)
- **+2.5s**: `Check Azure DevOps connection status` (Input: `/ado\n`)
- **+3.8s**: `Typo in /help command` (Input: `/hepl\n`)
- **+5.0s**: `Unknown slash command` (Input: `/invalid_command_xyz\n`)
- **+6.2s**: `Exit session` (Input: `/exit\n`)

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
sdlc-agent > /status
Active Sessions:                                                                                                        

 • #0 [running] Work Item #0 - Branch: agent/0-work                                                                     

sdlc-agent > /ado
Azure DevOps Status:                                                                                                    

 • Organization: Not set                                                                                                
 • Project: Not set                                                                                                     
 • Repository: Not set                                                                                                  
 • PAT Status: Missing                                                                                                  

To configure, run /ado setup <org> <project> [repo].                                                                    

sdlc-agent > /hepl
Unknown command: /hepl. Type /help for available commands.                                                              

sdlc-agent > /invalid_command_xyz
Unknown command: /invalid_command_xyz. Type /help for available commands.                                               

sdlc-agent > /exit
Goodbye!

```
