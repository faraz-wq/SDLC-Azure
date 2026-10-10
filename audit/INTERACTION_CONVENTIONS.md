# INTERACTION & CONVERSATIONAL CONVENTIONS

Tool-wide behavioral standards for interactive sessions (`agent chat` & `agent tui`).

---

## 1. Keybinding Map & Conflict Resolution

| Key Sequence | Context | Action | Behavior / Fallback |
|---|---|---|---|
| `Enter` | Single-line prompt | Submit command / message | Executes immediately if trimmed text is non-empty |
| `Alt+Enter` / `\`+`Enter` | Multiline prompt | Insert literal newline | Allows drafting multiline prompt without triggering execution |
| `Tab` | Empty or `/` prefix | Trigger autocomplete menu | Cycles through valid slash commands (`/help`, `/status`, `/ado`) |
| `Ctrl+C` | Prompt editing | Clear current input buffer | Erases typed text; does NOT terminate the session |
| `Ctrl+C` (twice < 1s) | Prompt editing | Exit application | Graceful shutdown: prints Goodbye and exits code 0 |
| `Ctrl+C` | Mid-generation / running | Abort in-flight task | Cancels LangGraph execution; saves checkpoint; returns to prompt |
| `Ctrl+D` | Empty prompt | Exit application | Standard POSIX EOF exit |
| `Ctrl+L` | Any time | Clear screen | Repaints prompt and context line at the top of the terminal |
| `Up` / `Down` | Prompt editing | Navigate input history | Cycles previous queries, skipping duplicate entries |

---

## 2. Slash-Command Grammar & Naming Rules

1. **Prefix Standard:** All in-session control commands must begin with `/` (`/run`, `/status`, `/clean`, `/ado`, `/help`, `/exit`).
2. **Case Insensitivity:** Slash commands are case-insensitive (`/ADO` and `/ado` behave identically).
3. **No Dead Ends:** Unknown commands or typos must run fuzzy matching (`difflib`) and return:
   `Unknown command '/hepl'. Did you mean '/help'?`
4. **Consistency with CLI:** Every top-level CLI command (`agent status`) must have a corresponding in-session slash command (`/status`).

---

## 3. Color & Glyph Policy with Accessibility Fallbacks

- **Semantic Colors:**
  - `Green`: Completed stages, successful checks (`✔`), done tickets
  - `Yellow`: Paused states (`waiting_on_human`), questions pending, warnings
  - `Cyan`: Informational headers, slash commands, prompt tokens
  - `Red`: Errors, destructive operations (`/clean`), failed test reports
- **NO_COLOR=1 Mode:**
  - When `NO_COLOR` is detected in the environment:
    - Zero ANSI color sequences are emitted.
    - All status states rely on plain ASCII text indicators: `[DONE]`, `[WAITING]`, `[ERROR]`.
    - Box-drawing unicode (`╭─╮`) degrades to ASCII borders (`+--+`).
- **Reduced Motion:**
  - In non-interactive or screen-reader modes, animated braille spinners (`⠋⠙⠹`) are replaced with a single static message: `[Processing...]`.

---

## 4. Verbosity & Output Pacing Standards

- **Low Verbosity (Default):**
  - Shows high-level stage transitions (`Ingesting ticket #42...`, `Scoring rubric...`).
  - Hides internal JSON payloads and raw tool calls.
- **Detailed Verbosity (`/verbose on` or `--debug`):**
  - Displays token counts, blast-radius scoring calculations, and subprocess return codes.
  - Formatted in dim grey text to preserve contrast hierarchy.

---

## 5. Non-Interactive / Scripting Fallback (`agent chat`)

If `agent chat` is invoked non-interactively (e.g. `cat prompt.txt | agent chat`):
1. The welcome banner is omitted.
2. The query is read from STDIN and executed once.
3. The response is printed to STDOUT.
4. The process exits with code 0 on success, code 1 on failure.

