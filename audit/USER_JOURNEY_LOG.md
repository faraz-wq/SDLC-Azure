# User Journey Log

**Note on this project:** SDLC-Azure is a CLI/TUI agentic pipeline tool, not a web application.
"User journeys" are the operator journeys: a developer using the CLI/TUI to process work items.
Phase 2 "End-User QA" is evaluated as a CLI/TUI ergonomics audit per the audit brief's note:
"CLI/API/library projects: Substitute equivalent evaluation: help text quality, flag consistency,
exit codes, error messages, defaults, output formats, discoverability, docs vs. actual behavior."

All journeys executed in the local environment on macOS. Pi CLI not installed. ADO credentials
not provided (integration flows simulated via test suite and code trace).

---

## Journey 1: First-Time Developer Setup

**Persona:** New developer joining the project, following README.md only.

### Steps

1. `git clone <repo>` — not tested (already cloned); assume standard.
2. Read `README.md`:
   - Content: "An Azure DevOps SDLC agent: work item in, draft pull request out. Built with LangGraph, human-approval interrupts, least-privilege guardrails, and evals."
   - **No setup instructions beyond this sentence.** No "how to install", no "how to run".
   - **Friction #1 (High):** README contains exactly 3 lines and links to nothing. No `uv sync`, no `.env.example` reference, no `agent --help`.
3. Discover `pyproject.toml` manually → find `uv sync` from AGENTS.md.
4. `uv sync` → succeeds cleanly. **[PASS]**
5. Look for `.env.example` → found, but README does not mention it.
   **Friction #2 (Medium):** First-time user doesn't know credentials are needed until the first run fails with a Python traceback.
6. `uv run pytest -q` → 34 passed. **[PASS]**
7. Try `uv run agent --help` → shows Typer help. **[PASS]**
8. Try `uv run agent run 42` with empty .env → get Python traceback from ADO HTTP 401.
   **Friction #3 (High):** No human-readable credential error. Traceback shown directly to user.

**Verdict: Would a real user succeed? PARTIAL.** 
A technical developer can set this up by reading AGENTS.md (not README.md). A non-technical evaluator would fail at step 2. Setup time ~15 min with docs gaps, ~5 min for someone familiar with uv.

---

## Journey 2: Run the Pipeline on a Work Item (Happy Path)

**Persona:** Developer with credentials set, wanting to process ticket #42.

### Steps

1. `cp .env.example .env` → fill in credentials. **[PASS]** (well-designed example)
2. `uv run agent run 42` → CLI calls `SessionManager.run_ticket(42)`.
3. Graph runs synchronously. **No output for potentially minutes.**
   **Friction #4 (High):** Complete silence. No "fetching ticket...", no "scoring rubric...", no spinner. User cannot distinguish hung from running.
4. If ticket score < 7.0: run pauses at `post_questions` interrupt. Session saved with `waiting_on_human`.
   Output: "Ticket #42 Execution Result: Status: waiting_on_human. Stage: clarify. Waiting on Human Input (questions): Please clarify..."
   **[PASS] Reasonable output structure.**
5. `uv run agent status` → shows ticket in table. **[PASS]**
6. `uv run agent approve 42` → submits answers. **Friction #5 (Medium):** The `approve` command in the CLI is defined in `cli/main.py` but the mechanism for providing answers interactively is unclear from `--help` output alone. The approve command takes no `--answer` flags; it only submits a pre-stored response.

**Verdict: Would a real user succeed? NO (without reading source code).** 
The approve flow is under-documented. The silence during graph execution is a usability failure.

---

## Journey 3: Respond to Clarification Questions via TUI

**Persona:** Power user wanting to use the Textual TUI for a better experience.

### Steps

1. `uv run agent tui` → TUI launches. Welcome message rendered. **[PASS]**
2. Sidebar shows session list. If no sessions: "[dim]No sessions[/dim]". **[PASS]**
3. Type `/run 42` in chat input → calls `session_mgr.execute_command("/run 42")`.
   - Same silent execution as Journey 2. No streaming progress in TUI either.
   - **Friction #6 (High):** The TUI freezes while the graph runs synchronously in the main Textual event loop. Textual is async-first; a synchronous `graph.invoke()` call will block the event loop and freeze the entire UI. This is UX-001 manifesting as a TUI freeze, not just a blank CLI.
4. After run: session appears in sidebar. Click on ticket 42 → interactive pane renders questions. **[PASS]**
5. Fill in answer inputs → click "Submit Answers". 
   - If any input widget failed to render: answer silently dropped (UX-002). **[FAIL]**
   - On success: notification shown, pane cleared. **[PASS]**
6. Sidebar auto-refreshes. **[PASS]**

**Verdict: Would a real user succeed? YES (if Pi is installed and ADO works), but with poor experience.** 
TUI freeze during graph execution is a P1 UX bug. Answer submission has a silent failure mode.

---

## Journey 4: Dry-Run Mode (no remote writes)

**Persona:** Developer wanting to test the pipeline locally without touching ADO.

### Steps

1. `uv run agent run 42 --dry-run` → passes `dry_run=True` to connectors.
2. `AzureTicketSource.get_ticket()` is **NOT** dry-run gated. It will still make live HTTP calls to fetch the ticket.
   **Friction #7 (High):** Dry-run mode is documented as "zero remote writes or pushes" but it still reads from ADO. This is acceptable per spec ("local worktree/test execution permitted"), but it means dry-run with no credentials still fails at ingest.
3. `post_comment` and `set_tag` → correctly no-ops. **[PASS]**
4. `create_draft_pr` → returns `PRRef(pr_id=0, url=".../pullrequest/dry-run")`. **[PASS]**
5. `push_branch` → logs "[DRY-RUN]" and returns. **[PASS]**

**Verdict: Would a real user succeed? YES with caveats.** 
Dry-run correctly prevents writes. But the user needs ADO read access (ticket fetch is live). Documentation should clarify this.

---

## Journey 5: Careless User — Garbage Ticket ID

**Persona:** Impatient user typing `agent run abc`.

### Steps

1. `uv run agent run abc` → Typer parses `abc` as string.
   Typer's integer type coercion rejects it before reaching application code.
   Output: "Error: Invalid value for 'TICKET_ID': 'abc' is not a valid integer."
   **[PASS] Good error message from Typer.**
2. `uv run agent run 0` → zero ticket ID reaches `SessionManager.run_ticket(0)`.
   → `get_ticket(0)` makes HTTP call to ADO for item 0, which will return 404.
   → urllib raises `HTTPError(404)` → unhandled → Python traceback shown.
   **Friction #8 (Medium):** Zero/negative ticket IDs are not validated before ADO call; raw traceback shown.

**Verdict: Would a real user succeed? NO for edge cases.** 
Basic Typer validation catches type errors. Domain validation (valid ticket ID range) is absent.

---

## Journey 6: Hostile User — Branch Name Injection

**Persona:** Adversarial user attempting to create a PR from main.

### Steps

1. Attempt to inject a malicious branch name by modifying the session state SQLite directly
   and setting `branch_name = "main"`.
2. `raise_draft_pr_node` calls `pr_host.create_draft_pr(branch="main", ...)`.
3. `AzurePRHost.create_draft_pr` checks: `_AGENT_BRANCH_REGEX.match("main")` → no match.
   Raises `ValueError: "Refusing to create PR from branch 'main'"`. **[PASS] Guard holds.**
4. Attempt `agent/../main` → same guard rejects it. **[PASS]**

**Verdict: Branch name guards are robust.** Three independent enforcement points (validate_branch_name, push_branch, create_draft_pr) all reject non-conforming names.

---

## Summary Table

| Journey | Persona | Outcome | Key Friction |
|---|---|---|---|
| 1. Setup | First-time dev | [WARN] Partial | README has no instructions; credential error is a traceback |
| 2. Run pipeline | Standard user | [FAIL] No | Silent execution; approve flow undiscoverable |
| 3. TUI clarification | Power user | [WARN] Partial | TUI freezes during graph execution; silent answer loss |
| 4. Dry-run | Cautious dev | [PASS] Yes (with caveat) | Reads are live; docs should clarify |
| 5. Garbage input | Careless user | [WARN] Partial | Type errors caught; domain validation absent |
| 6. Hostile input | Adversarial | [PASS] Yes | Branch guard holds across all entry points |

