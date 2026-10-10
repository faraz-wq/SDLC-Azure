# INTERACTIVE CONVERSATIONAL IMPROVEMENT PLAN

Before/after terminal screens, implementation efforts, and rollout priorities.

---

## 1. Quick Wins (High Impact, Low Effort — Recommended for Immediate Approval)

### Quick Win 1: Safe Confirmation on `/clean` (`INT-F001`)
- **Dimension:** Permissions & Safety
- **Effort:** Small (~15 minutes)
- **Risk:** Zero
- **Before:**
  ```text
  sdlc-agent > /clean 42
  ✔ Cleaned session and worktree for ticket #42.
  ```
- **After:**
  ```text
  sdlc-agent > /clean 42
  ⚠ Are you sure you want to delete session and worktree for Ticket #42? [y/N]: n
  Action cancelled.

  sdlc-agent > /clean 42
  ⚠ Are you sure you want to delete session and worktree for Ticket #42? [y/N]: y
  ✔ Cleaned session and worktree for Ticket #42.
  ```

---

### Quick Win 2: Graceful `Ctrl+C` Line Clearing (`INT-F002`)
- **Dimension:** Control & Interruption
- **Effort:** Small (~15 minutes)
- **Risk:** Zero
- **Before:**
  ```text
  sdlc-agent > what was the... ^C
  Exiting SDLC Agent. Goodbye!
  (Process abruptly exits to bash)
  ```
- **After:**
  ```text
  sdlc-agent > what was the... ^C
  (Input cleared)
  sdlc-agent >
  (Press Ctrl+C again or type /exit to quit)
  ```

---

### Quick Win 3: Fuzzy Typo Recovery for Slash Commands (`INT-F005`)
- **Dimension:** Error Quality & Recovery
- **Effort:** Small (~20 minutes)
- **Risk:** Zero
- **Before:**
  ```text
  sdlc-agent > /hepl
  Unknown command: `/hepl`. Type `/help` for available commands.
  ```
- **After:**
  ```text
  sdlc-agent > /hepl
  Unknown command `/hepl`. Did you mean `/help`?
  Type `/help` for a full list of commands.
  ```

---

### Quick Win 4: Helpful Auth Guidance on 401 Queries (`INT-F006`)
- **Dimension:** Polish & Trust
- **Effort:** Small (~15 minutes)
- **Risk:** Zero
- **Before:**
  ```text
  sdlc-agent > Can you review the files?
  ⠋ Thinking...
  Error communicating with AI assistant: HTTP Error 401: Unauthorized
  ```
- **After:**
  ```text
  sdlc-agent > Can you review the files?
  ⠋ Thinking...
  ╭─ Authentication Required ──────────────────────────────────────────────────╮
  │ Could not communicate with OpenCode Go inference API.                      │
  │ Reason: HTTP 401 Unauthorized (Invalid or missing API key).                │
  │                                                                            │
  │ Next Step:                                                                 │
  │   Set OPENCODE_API_KEY in your .env file, or configure your credentials.   │
  ╰────────────────────────────────────────────────────────────────────────────╯
  ```

---

## 2. Structural Redesigns

### Structural Redesign 1: Persistent Status Line / Bottom Bar (`INT-F003`)
- **Dimension:** Status & Feedback
- **Effort:** Medium (~1.5 hours)
- **Risk:** Low (improves prompt rendering)
- **Description:** Replace the raw `input()` loop with a persistent status bar displayed beneath the conversation, keeping vital context pinned to the screen.

---

### Structural Redesign 2: Multiline Input & Autocomplete via `prompt_toolkit` (`INT-F004`)
- **Dimension:** Input Experience
- **Effort:** Medium (~2 hours)
- **Risk:** Low
- **Description:** Implement `PromptSession` with:
  1. Tab completion for `/help`, `/status`, `/ado`, `/run`, `/clean`
  2. Bracketed paste handling (multi-line code pastes safely without premature execution)
  3. Up/Down persistent history navigation across sessions

---

## 3. Implementation Dependency Map

```
[Phase 1: Quick Wins - ~1 Hour Total]
  INT-F001 (Safe /clean confirmation)
      │
      ├─► INT-F002 (Ctrl+C graceful buffer clear)
      ├─► INT-F005 (Fuzzy typo matching with difflib)
      └─► INT-F006 (Human-friendly 401 auth box)

[Phase 2: Structural Polish - ~3 Hours Total]
  INT-F004 (prompt_toolkit session & bracketed paste)
      │
      └─► INT-F003 (Persistent status toolbar)
```
