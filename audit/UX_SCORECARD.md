# INTERACTIVE CONVERSATIONAL CLI & TUI UX SCORECARD

**Tool Evaluated:** Azure DevOps SDLC Agent Interactive Interfaces (`agent chat` / REPL & `agent tui`)  
**Auditor:** Senior TUI/CLI Product Designer & QA Engineer  
**Date:** 2026-10-10  
**Test Harness:** Real Pseudo-Terminal (PTY) emulation in isolated sandbox (`audit/sandbox/fakerepo`)  
**Reference Evidence:** Session Transcripts `01` through `08` in [`audit/session_transcripts/`](file:///Users/faraz/Projects/SDLC-Azure/audit/session_transcripts/)  

---

## Overall Conversational UX Grade: 4.4 / 10

**Calculation Method:** Weighted Average (Scores 1 to 10)  
*For an agentic developer assistant, safety, control, status feedback, and input reliability are weighted most heavily:*
- **Safety, Permissions & Consent (20%):** 3.0 / 10
- **Control & Interruption (15%):** 4.0 / 10
- **Status & Feedback (15%):** 4.0 / 10
- **Input Experience & Autocomplete (15%):** 4.0 / 10
- **First-Run, Help & Discoverability (15%):** 6.0 / 10
- **Output, Formatting & Streaming (10%):** 6.0 / 10
- **Robustness, Performance & Environment (10%):** 5.0 / 10

$$ \text{Weighted Grade} = (3.0 \times 0.20) + (4.0 \times 0.15) + (4.0 \times 0.15) + (4.0 \times 0.15) + (6.0 \times 0.15) + (6.0 \times 0.10) + (5.0 \times 0.10) = 4.40 / 10 $$

---

## Dimension Breakdown (15 Dimensions)

| # | Dimension | Score (1-10) | One-Sentence Justification | Session Evidence |
|---|---|:---:|---|---|
| 1 | **First-run & Onboarding** | **5 / 10** | Welcome panel lists available slash commands clearly, but there is no setup wizard, no directory/branch status line, and no indication whether authentication is configured until a query fails. | `01_first_contact.md` |
| 2 | **Discoverability** | **6 / 10** | Slash commands `/ado`, `/run`, `/status`, `/clean`, `/help`, `/exit` are visible in the welcome box and `/help`, but keyboard shortcuts and sub-options have zero in-tool visibility. | `01_first_contact.md`, `02_slash_commands_and_typos.md` |
| 3 | **Input Experience** | **4 / 10** | Standard terminal `input()` lacks multiline entry (Enter always submits), autocomplete (`/` or Tab) does not exist, and pasting embedded newlines immediately triggers premature execution. | `03_input_stress_and_edge_cases.md` |
| 4 | **Output & Streaming Quality** | **6 / 10** | Rich markdown formatting renders headings and bullet points cleanly, but thinking indicators freeze during blocking network calls and no token streaming occurs. | `01_first_contact.md`, `05_natural_query_agent_chat.md` |
| 5 | **Status & Feedback** | **4 / 10** | No persistent status line or footer indicating active git branch, token/context budget, or LLM model; `/status` prints a disconnected dump into the scrollback. | `02_slash_commands_and_typos.md`, `08_tui_app_interface.md` |
| 6 | **Control & Interruption** | **4 / 10** | Pressing `Ctrl+C` at the prompt immediately terminates the entire application (`Exiting SDLC Agent. Goodbye!`) without clearing the current line or offering a cancel/resume prompt. | `04_interruption_signals.md` |
| 7 | **Permissions & Safety** | **3 / 10** | In-session `/clean <id>` wipes active git worktrees and session tracking databases immediately without confirmation or diff preview, and natural language queries trigger un-consented subprocesses. | `06_in_session_clean_command.md` |
| 8 | **Session & Context Management** | **5 / 10** | Sessions persist across restarts in SQLite, but the chat interface has no `/compact`, `/clear`, `/context`, or session resume switch (`/resume <id>`). | `02_slash_commands_and_typos.md` |
| 9 | **Error Quality & Recovery** | **4 / 10** | Typos in slash commands (`/hepl`) report a dead-end message with zero fuzzy suggestions, and unauthenticated queries output raw `HTTP Error 401: Unauthorized` strings. | `02_slash_commands_and_typos.md`, `05_natural_query_agent_chat.md` |
| 10 | **Consistency** | **5 / 10** | Slash commands in REPL use `/ado`, but the CLI counterpart does not exist; exit accepts `/exit`, `/quit`, `exit`, `quit`, but other commands strictly demand leading slashes. | `02_slash_commands_and_typos.md` |
| 11 | **Robustness & Terminal Citizenship**| **5 / 10** | Restores terminal cursor properly on exit, but 40x15 small terminal squashes welcome text into an awkward vertical strip without adapting layout. | `07_small_terminal_and_no_color.md` |
| 12 | **Performance Feel** | **6 / 10** | Instant local response for `/help` and `/status`, but natural queries block the single Python thread with synchronous spinner animations. | `05_natural_query_agent_chat.md` |
| 13 | **Scriptability** | **3 / 10** | Conversational REPL cannot be driven in headless pipe mode (`echo "query" | agent chat` prints full welcome banner and goodbye, discarding piped intent). | `01_first_contact.md` |
| 14 | **Accessibility & Environment Support** | **5 / 10** | Honors `NO_COLOR=1` cleanly via Rich, but screen readers are bombarded with animated braille spinner characters during processing. | `07_small_terminal_and_no_color.md` |
| 15 | **Polish & Trust** | **4 / 10** | Unhandled 401 error messages and lack of confirmation on destructive actions make the tool feel like an early prototype rather than an enterprise SDLC assistant. | `05_natural_query_agent_chat.md`, `06_in_session_clean_command.md` |

---

## Per-Persona Verdicts

- **First-Time User:** **FAIL (Verdict: ✗ NO)**  
  *Why:* The user sees the welcome box and types a natural query like *"Review this repo"*. It spins for 2 seconds and prints `Error communicating with AI assistant: HTTP Error 401: Unauthorized` with no hint that `OPENCODE_API_KEY` or `AZURE_DEVOPS_PAT` must be configured in `.env`.
- **Daily Power User:** **FAIL (Verdict: ✗ NO)**  
  *Why:* No tab completion for commands, no `@file` syntax, multiline code snippets cannot be pasted without accidental immediate submission, and no persistent branch/model status bar exists.
- **Cautious / Security-Minded User:** **FAIL (Verdict: ✗ NO)**  
  *Why:* The tool has no consent boundary or confirmation prompt when running `/clean` or modifying files; permissions are neither displayed nor revokable.
- **Impatient User (interrupts & pastes junk):** **FAIL (Verdict: ✗ NO)**  
  *Why:* Pressing `Ctrl+C` immediately kills the session and dumps the user back to the OS shell instead of cancelling the current command. Pasting text with newlines causes cascading line submissions.
- **CI / Script Author:** **FAIL (Verdict: ✗ NO)**  
  *Why:* Non-interactive piping into `chat` or `tui` does not execute queries deterministically; there is no headless print mode (`-p` / `--non-interactive`).

---

## Top 5 Interactive UX Problems

1. **INT-001 (Critical): Destructive `/clean` Command Has Zero Confirmation.** Inside the chat session, typing `/clean 42` permanently wipes the git worktree and SQLite session database instantly without confirmation, undo, or diff preview.
2. **INT-002 (High): `Ctrl+C` Immediately Kills the Session.** In conversational tools (Claude Code, aider, bash), `Ctrl+C` clears the input buffer or cancels the active generation. Here, `Ctrl+C` at an idle prompt instantly exits the entire process, destroying unsaved context.
3. **INT-003 (High): Missing Persistent Status Bar & Context Line.** The prompt is a bare `sdlc-agent > ` line. Users have no visibility into active repo branch, model in use, token/budget limits, or whether Azure DevOps PAT is authenticated.
4. **INT-004 (High): Bracketed Paste / Multiline Input Failure.** Entering newlines or pasting multiline text immediately fires line-by-line submission in `console.input()`, causing unintended execution of incomplete queries.
5. **INT-005 (Medium): Dead-End Slash Command Typo Recovery.** Typing `/hepl` or `/stat` outputs `Unknown command: /hepl. Type /help for available commands.` with zero fuzzy matching or suggestions (e.g. `Did you mean /help?`).
