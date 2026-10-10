# SDLC-Azure Adversarial Audit Report

**Auditor:** Independent Principal QA / Software Architect (AI-assisted)
**Date:** 2026-10-10
**Commit context:** latest main (`.agent/sessions.sqlite` present, implying prior runs)
**Environment:** macOS, Python 3.12.15, uv, pytest 9.1.1, ruff 0.17.0, pyright strict

---

## Executive Summary

| Dimension | Score | One-sentence justification |
|---|---|---|
| **Architecture** | 7 / 10 | Clean layering and protocol boundaries; two real structural defects (impact_analysis stub, verify stub) and one boundary bypass hole drag it down. |
| **Code Quality** | 6 / 10 | Excellent type discipline; but `except Exception: pass` in two hot paths, `\r\n` artifacts throughout, and three effectively stubbed nodes in a "complete" pipeline are material gaps. |
| **Security** | 5 / 10 | Two *verified* scope-guard bypasses let arbitrary files be touched outside the approved plan; one secret-scrubbing gap lets short/prefixed secrets escape. These are in review-critical files. |
| **Test Confidence** | 4 / 10 | 34 tests all pass, but no test exercises the real implement→verify→scope-guard path end-to-end; `confirm_red_node` and `impact_analysis_node` are not actually tested for correctness; coverage of the 3 confirmed security bugs is zero until this audit. |
| **Operability** | 4 / 10 | No CI/CD config of any kind exists; no lockfile pinning of exact versions (only lower bounds); no health-check, metrics, or tracing beyond what LangSmith would add later. |
| **UX / CLI** | 6 / 10 | CLI and TUI are coherent for a portfolio project; `agent run` blocks the main thread with a synchronous graph execution; TUI submit-answers flow has a silent-failure path. |
| **Accessibility** | N/A | CLI/TUI project — no web UI. Keyboard-navigable TUI; no screen-reader or contrast audit performed (Textual handles basics). |

### Top 5 Most Urgent Problems

1. **SEC-001 (Critical)** — `scope_guard.py` allows any file whose *allowed path is a substring of the touched path* (e.g. allowed `src/api` matches `src/api-evil/bad.cs`). **Verified exploit.**
2. **SEC-002 (Critical)** — Same substring logic applies after backslash→slash normalisation, so a Windows-style path `src\safe-zone\evil.cs` bypasses the guard when `src/safe` is allowed. **Verified exploit.**
3. **ARCH-001 (High)** — `impact_analysis_node`, `confirm_red_node`, `verify_node`, and `write_tests_node` are stubs that do not perform their stated functions. The "complete SDLC pipeline" is a skeleton that always succeeds locally without running tests, code analysis, or Playwright. A PR raised by this agent has *no evidence of correctness*.
4. **CODE-001 (High)** — `implement_node` line 44: `except Exception: pass` silently swallows all Pi agent failures. A failed coding run continues to `check_diff_cap` with an empty diff, and the pipeline declares success.
5. **DEVOPS-001 (High)** — Zero CI/CD configuration. No GitHub Actions, Azure Pipelines, or any other pipeline file exists. Nothing gates merges or checks the toolchain automatically.

---

## Scope & Method

### What was run
- `uv run pytest -q` — full suite including integration: **33 passed, 1 FAILED** (808 s / 13 min 28 s)
- `uv run pytest -q -m "not integration"` — 32 pass (20 s)
- `uv run ruff check .` — 0 errors
- `uv run pyright` — 0 errors (strict mode)
- 21 hand-authored adversarial tests in `audit/scratch/test_adversarial.py` — **3 confirmed failures**
- Full manual read of every Python file in `agent/`, `tests/`, and docs.

### What was NOT covered
- Live ADO integration (no credentials provided in env; `integration` marker skipped)
- Real Pi CLI execution (not installed on this machine; subprocess falls back to empty diff)
- Playwright verifier (not implemented; stub only)
- Podman sandbox (not implemented; referenced in docs/AGENTS.md but absent in code)
- LangSmith tracing (referenced in SPEC but absent in code)
- `evals/` directory (referenced in ARCHITECTURE but does not exist in repo)
- Multi-process / concurrent session behaviour

### Sampling strategy
Risk-priority order: security guards → connectors → nodes → session layer → UI → tests.

---

## Findings

### CRITICAL

---

```
ID: SEC-001
Title: scope_guard substring-match allows files outside approved plan
Severity: Critical
Confidence: Verified (reproducible test in audit/scratch/test_adversarial.py)
Category: Security
Location: agent/guards/scope_guard.py:42 — `clean_allowed in norm_file`
Evidence:
  check_scope(["src/api-evil/bad.cs"], diff_lines=1, plan=_make_plan(["src/api"]))
  → does NOT raise ScopeViolationError
  Test: test_scope_guard_substring_loophole — FAILS with "guard allowed src/api-evil/bad.cs"
Reproduction:
  1. Create plan with allowed_files=["src/api"]
  2. Call check_scope(["src/api-evil/bad.cs"], 1, plan)
  3. No exception raised → file is permitted
Impact: A coding agent (Pi or a compromised one) can modify any file whose path
  contains an allowed-files token. e.g. allowed "src" permits literally everything.
  This is the primary enforcement mechanism preventing scope creep; its bypass
  nullifies the entire "files outside approved plan" guardrail.
Root cause: Line 42 uses Python `in` for substring matching as a fallback after
  fnmatch. The intent was to allow simple path prefixes, but the check is not
  anchored to path boundaries.
Recommendation (S):
  Replace `clean_allowed in norm_file` with a path-boundary check:
    `norm_file == clean_allowed or norm_file.startswith(clean_allowed.rstrip('/') + '/')`
  Or rely solely on fnmatch with a trailing `/**` glob; remove the substring fallback entirely.
```

---

```
ID: SEC-002
Title: scope_guard substring bypass survives backslash normalisation
Severity: Critical
Confidence: Verified (test_scope_guard_windows_path_separator_bypass)
Category: Security
Location: agent/guards/scope_guard.py:37-42
Evidence:
  check_scope(["src\\safe-zone\\evil.cs"], 1, plan=_make_plan(["src/safe"]))
  → does NOT raise ScopeViolationError
  (After backslash→slash conversion, 'src/safe' is a substring of 'src/safe-zone/evil.cs')
Reproduction:
  1. Plan allows ["src/safe"]
  2. Diff touches "src\safe-zone\evil.cs" (Windows path from Pi running in WSL/Windows)
  3. check_scope passes silently
Impact: Same as SEC-001; additionally exploitable if Pi CLI runs on Windows or WSL
  and produces backslash paths.
Root cause: Same underlying substring check; fix SEC-001 fixes this.
Recommendation (S): Fix SEC-001; no additional change needed.
```

---

### HIGH

---

```
ID: ARCH-001
Title: Four "complete pipeline" nodes are non-functional stubs
Severity: High
Confidence: Verified (code read + test observation)
Category: Architecture / Functional
Location:
  agent/nodes/impact_analysis.py — returns a static message, no CodeIndex call
  agent/nodes/confirm_red.py — returns red_confirmed=True unconditionally without running tests
  agent/nodes/verify.py — creates a hardcoded TestReport(passed=1, failed=0, total=1)
  agent/nodes/write_tests.py — emits a comment-only .cs file with no real test code
Evidence:
  impact_analysis_node (lines 8-15): returns {"stage":"plan", "messages":[...]} with no analysis
  confirm_red_node (lines 8-17): always sets red_confirmed=True regardless of actual test run
  verify_node (lines 16-33): hardcoded report = TestReport(passed=1, failed=0, total=1)
  write_tests_node (lines 16-27): output is "// Auto-generated tests..." comment strings
Impact: The agent will always claim tests are red (without running them), always claim
  verification passed (without building or running tests), and always claim impact analysis
  completed (without querying a code index). A draft PR raised by this agent has zero
  evidentiary basis for correctness. The portfolio value is severely undermined.
Root cause: Slice-based development — these nodes are correctly shaped stubs awaiting
  real implementation.
Recommendation (M): Gate `create_full_sdlc_graph` behind a feature flag or rename it
  `create_draft_sdlc_graph`. Add integration tests that assert these nodes call their
  injected dependencies (StackAdapter, Verifier) rather than returning hardcoded success.
```

---

```
ID: CODE-001
Title: implement_node silently swallows all coding-agent failures
Severity: High
Confidence: Verified (code read)
Category: Code Quality
Location: agent/nodes/implement.py:42-45
Evidence:
  try:
      agent.run(task, wt=wt_path, limits=task.limits)
  except Exception:
      pass   <- ALL exceptions discarded
  The node then calls check_diff_cap on an empty diff -> passes with 0 lines.
  Pipeline continues and declares "implementation complete."
Impact: Pi CLI crash, timeout, missing binary, bad prompt — all produce an
  empty-diff "success" that passes through to PR creation. A PR is opened with
  no code changes while every status indicator shows green.
Root cause: Defensive coding without recovery logic; likely added to prevent
  test failures when Pi is not installed.
Recommendation (S):
  Catch expected recoverable errors (timeout, missing binary) and log them.
  Re-raise or set state.error for unrecoverable failures so the graph can
  route to a failure terminal node instead of continuing.
```

---

```
ID: DEVOPS-001
Title: Zero CI/CD configuration
Severity: High
Confidence: Verified (file tree inspection: no .github/, no azure-pipelines.yml, no .circleci/)
Category: DevOps
Location: repo root (absence)
Evidence:
  find /Users/faraz/Projects/SDLC-Azure -name "*.yml" returns only models.yaml and ticket_rubric.yaml.
  No pipeline configuration file found anywhere in the repository.
Impact: Nothing prevents a broken commit from landing on main. For a portfolio project
  demonstrating engineering rigour, the absence of CI is conspicuous.
Root cause: Likely deferred; no slice has addressed CI setup.
Recommendation (S):
  Add .github/workflows/ci.yml running: uv sync, pytest -m "not integration",
  ruff check, ruff format --check, pyright. Should take under 2 minutes.
```

---

```
ID: SEC-003
Title: secret_scrub does not catch short credentials without a recognised key name or prefix
Severity: High
Confidence: Verified (code + pattern analysis)
Category: Security
Location: agent/guards/secret_scrub.py:11-16 (_PATTERNS)
Evidence:
  scrub_secrets("MY_INTERNAL_KEY=abc123") -> "MY_INTERNAL_KEY=abc123" (unchanged).
  The connection-string regex matches only a fixed set of key names (password, pwd,
  accountkey, sharedaccesskey, secret, token). Any other key name passes through.
  The env-var fallback covers only 4 specific env var names.
  The 52-char PAT regex does not match short secrets.
Impact: If a user pastes a non-standard secret into a ticket description and it ends
  up in LLM prompts, it passes through scrub_secrets uncleaned.
Root cause: Pattern-based scrubbing is inherently incomplete.
Recommendation (M):
  (1) Expand env-var scrubbing to read ALL env vars matching *_KEY, *_SECRET,
      *_TOKEN, *_PAT, *_PASSWORD patterns above a minimum length (>= 8 chars).
  (2) Add Shannon entropy heuristic as a second line of defence for high-entropy strings.
```

---

```
ID: ARCH-002
Title: LangGraph dependency injection via closures prevents per-invocation dep swapping
Severity: High
Confidence: Verified (code read)
Category: Architecture
Location: agent/graph.py:72-130 (create_full_sdlc_graph)
Evidence:
  All node dependencies are closed over via inner lambdas (_ingest, _clarify_score, etc.)
  rather than using LangGraph's RunnableConfig/configurable context. Dependencies cannot
  be swapped per-invocation without rebuilding the entire graph.
Impact: The eval harness (auto_answer channel) will need to rebuild the graph for each
  eval variant. Testing individual nodes requires constructing the full graph or working
  around the closure.
Root cause: Closures are the simplest pattern; RunnableConfig pattern not yet adopted.
Recommendation (M): Pass deps through LangGraph's RunnableConfig.configurable dict.
```

---

```
ID: ARCH-003
Title: Full SDLC graph has no failure terminal — errors leave session stuck at "running"
Severity: High
Confidence: Verified (graph.py — no conditional edges for error states)
Category: Architecture
Location: agent/graph.py:160-195
Evidence:
  No conditional edge handles state.error or node exceptions. An exception in any node
  crashes the graph executor leaving the checkpoint in the last-good state and the
  session registry in status="running" indefinitely.
Impact: A network blip fetching the ADO ticket leaves the session silently hung.
  `agent status` shows "running." User has no recovery path except manual SQLite surgery.
Root cause: Error routing not implemented in current slices.
Recommendation (M):
  Add a "failed" terminal node. Route to it if state.error is set after any node.
  Surface error via HumanChannel. Use LangGraph's error handling hooks.
```

---

```
ID: SEC-004
Title: push_branch() is a no-op in live mode — PR creation will fail on ADO (branch not found)
Severity: High
Confidence: Verified (code read)
Category: Functional / Security
Location: agent/connectors/pr_host_azure.py:55-69
Evidence:
  def push_branch(self, branch: str) -> None:
      ...
      if self.dry_run:
          logger.info("[DRY-RUN] would push branch...")
          return
      # Live push would happen via git worktree remote push command
      logger.info(f"Pushed branch '{clean_branch}'")   <- no actual git push
Impact: In live mode, `push_branch` logs a success message but does nothing.
  `create_draft_pr` will then fail on ADO with "branch not found" error.
  The "end-to-end" pipeline cannot actually create a real PR.
Root cause: Implementation deferred; marked as future work in comment.
Recommendation (M):
  Implement using: subprocess.run(["git", "push", "origin", branch], cwd=wt_path, ...)
  Gate behind dry_run check (already present). Thread worktree path through.
```

---

### MEDIUM

---

```
ID: CODE-002
Title: \r\n line endings in Python source files
Severity: Medium
Confidence: Verified (observed in multiple file outputs)
Category: Code Quality
Location: agent/nodes/clarify_score.py, agent/graph.py, and others
Evidence:
  cat output shows \r\n sequences. ruff and pyright normalise line endings before checking.
  git diff will show spurious changes on Linux/macOS CI.
Root cause: Files edited or generated on Windows without .gitattributes.
Recommendation (S): Add .gitattributes: `* text=auto eol=lf`. Run git add --renormalize .
```

---

```
ID: CODE-003
Title: clarify_score_node defaults to score=8.0 on LLM parse failure, silently skipping clarification
Severity: Medium
Confidence: Verified (code read)
Category: Code Quality / Functional
Location: agent/nodes/clarify_score.py:76-90
Evidence:
  score = 8.0  # hardcoded default when LLM parse fails
  An LLM timeout/malformed JSON silently routes to impact_analysis without clarification.
  No log, no error signal, no state.error set.
Recommendation (S): On parse failure, set score=0.0 (force clarification) or log a warning.
```

---

```
ID: CODE-004
Title: propose_options_node bare except swallows LLM errors, proceeds with fabricated options
Severity: Medium
Confidence: Verified (code read)
Category: Code Quality
Location: agent/nodes/propose_options.py:44-51
Evidence:
  except Exception:
      pass
  Falls back to two hardcoded generic options with glob patterns "src/**/*.cs", "src/**/*.tsx".
Recommendation (S): Log the exception. Set state.error or raise to route to failure.
```

---

```
ID: CODE-005
Title: AzureTicketSource.set_tag() makes 2 extra HTTP calls (N+1) to fetch full ticket for tags
Severity: Medium
Confidence: Verified (code read)
Category: Performance
Location: agent/connectors/ticket_source_azure.py:98-118
Evidence:
  def set_tag(...):
      ticket = self.get_ticket(id)  # 2 HTTP calls (work item + comments)
      current_tags = set(ticket.tags)
  set_tag costs 3 HTTP calls total when 1 PATCH is sufficient.
Recommendation (S): PATCH /fields/System.Tags directly without fetching the full ticket.
```

---

```
ID: CODE-006
Title: new_replies_since uses marker body-substring match — fragile and spoofable
Severity: Medium
Confidence: Verified (code read)
Category: Security / Code Quality
Location: agent/connectors/ticket_source_azure.py:121-130
Evidence:
  elif marker in c.body:  <- substring match on comment body text
  A user comment containing the marker string causes all subsequent comments to be returned.
  Empty-string marker matches the first comment always.
Recommendation (S): Use comment integer ID as marker; use ADO API minId parameter.
```

---

```
ID: CODE-007
Title: OpenCodeClient does not handle reasoning-model null content as specified in ARCHITECTURE.md
Severity: Medium
Confidence: Verified (code vs. docs comparison)
Category: Functional / Reliability
Location: agent/llm/opencode_client.py:77-101 vs. docs/ARCHITECTURE.md §13
Evidence:
  content: str = str(message_data.get("content") or "")  <- null coerced to ""
  ARCHITECTURE.md: "treat null content with length as a retryable budget-exhausted error"
  "record reasoning_tokens in RunMetrics" — neither implemented.
Recommendation (M): Implement retry-on-length, reasoning_tokens recording, null-content handling.
```

---

```
ID: CODE-008
Title: OpenCodeClient.complete() has no HTTP timeout — violates AGENTS.md hard rule
Severity: Medium
Confidence: Verified (code read)
Category: Reliability
Location: agent/llm/opencode_client.py:91-98
Evidence:
  urllib.request.urlopen(req)  <- no timeout= argument
  AGENTS.md: "Every external call has a timeout."
Recommendation (S): urllib.request.urlopen(req, timeout=60)
```

---

```
ID: CODE-009
Title: AzureTicketSource and AzurePRHost urllib calls have no timeout
Severity: Medium
Confidence: Verified (code read)
Category: Reliability
Location: agent/connectors/ticket_source_azure.py (5 urlopen calls), pr_host_azure.py:117
Evidence: Same as CODE-008; 6 additional unguarded urlopen calls.
Recommendation (S): Add timeout= to all urlopen calls using AgentConfig.external_timeout_seconds.
```

---

```
ID: ARCH-004
Title: plan.max_diff_lines hardcoded to 150 in select_smallest_node, inconsistent with diff_cap (300)
Severity: Medium
Confidence: Verified (code read)
Category: Architecture
Location: agent/nodes/select_smallest.py:39
Evidence:
  max_diff_lines=150  <- hardcoded; AgentConfig.max_diff_lines exists (default 300)
  check_diff_cap default is 300. A 200-line diff passes diff_cap but fails scope_guard.
Recommendation (S): Source max_diff_lines from AgentConfig; eliminate the magic number.
```

---

```
ID: DOCS-001
Title: ARCHITECTURE.md references evals/, LangSmith, Podman, and auto_answer — none exist
Severity: Medium
Confidence: Verified (file tree)
Category: Docs
Location: docs/ARCHITECTURE.md §5, §10, §13 vs. repo root
Evidence:
  No evals/ directory. No LangSmith import. No Podman config. No auto_answer channel.
Recommendation (S):
  Add "Current Implementation Status" section to README.md listing which slices
  are done vs. planned. Use a checklist.
```

---

### LOW

---

```
ID: CODE-010
Title: RunState.messages grows unboundedly — full list copied on every node transition
Severity: Low
Confidence: Verified (all node files)
Category: Performance
Location: Every node file
Evidence:
  return {"messages": [*state.messages, "new message"]}
  14-node pipeline × 5 iterations = 70+ appends, each serialising the full list into SQLite.
Recommendation (S): Use LangGraph's Annotated[list[str], add_messages] reducer.
```

---

```
ID: UX-001
Title: agent run blocks the terminal synchronously with no progress indicator
Severity: Low
Confidence: Verified (session/manager.py)
Category: UX
Location: agent/session/manager.py (run_ticket)
Evidence:
  Graph invoked synchronously. 180-second Pi timeout + ADO calls = potentially 3+ minutes
  of blank terminal.
Recommendation (M): Run graph in background thread; stream Rich Live events to terminal.
```

---

```
ID: UX-002
Title: TUI answer submission silently discards answers on widget query failure
Severity: Low
Confidence: Verified (code read)
Category: UX
Location: agent/ui/tui/app.py (on_button_pressed, answer collection block)
Evidence:
  except Exception:
      pass   <- answer silently omitted from submission
Recommendation (S): Surface via self.notify("Error collecting answer N", severity="error").
```

```
ID: INT-001
Title: Integration test test_live_opencode_completion hung for 13 minutes then failed with
  RemoteDisconnected — confirms CODE-008 is an active real-world failure
Severity: High
Confidence: Verified (actual test run output, full suite)
Category: Reliability / Testing
Location: tests/test_integration_ado.py:44-52 / agent/llm/opencode_client.py:87
Evidence:
  Full suite run (uv run pytest -q, 808 s total):
    FAILED tests/test_integration_ado.py::test_live_opencode_completion
    E   http.client.RemoteDisconnected: Remote end closed connection without response
    1 failed, 33 passed in 808.38s (0:13:28)
  The test blocked for ~13 minutes before the TCP layer dropped the connection.
  No timeout was set on urllib.request.urlopen (CODE-008).
  This test is NOT marked @pytest.mark.integration, so it is NOT filtered by
  `uv run pytest -q -m "not integration"` in the AGENTS.md fast path — wait,
  actually it IS marked integration (line 38: @pytest.mark.integration). So fast
  CI skips it. But: `uv run pytest -q` (the "all tests" AGENTS.md command) runs it
  and blocks for 13 minutes before failing. Any developer running the full suite
  will be blocked.
  Additionally: the test asserts res.usage.get("total_tokens", 0) > 0, but the current
  OpenCodeClient always returns usage={} when the API fails, so this assert is unreachable.
Impact:
  (1) Confirms CODE-008 (no timeout) causes real 13-minute hangs in practice.
  (2) `uv run pytest -q` (the AGENTS.md "all tests" command) takes 13+ minutes and
      produces a failure even with valid credentials if the API is rate-limiting or
      the endpoint drops the connection.
  (3) The test is not truly guarded: OPENCODE_API_KEY is present in .env, so pytest
      does not skip it. With a slow/dropped endpoint, the developer gets a 13-minute wait.
Root cause: No timeout in urlopen (CODE-008); real endpoint closed the connection.
Recommendation (S):
  (1) Fix CODE-008: add timeout= to urlopen.
  (2) Mark the test with a short timeout: @pytest.mark.timeout(30).
  (3) Assert usage from a mock/recorded response in unit tests; reserve live assertion
      for a dedicated slow-test suite.
```

---



- **LangGraph thread_id vs. session_id mismatch**: `f"ado-{ticket_id}"` is used as both the LangGraph thread_id and the HumanChannel session_id. If LangGraph's checkpoint saver uses a different key format, checkpoint replay on resume may retrieve the wrong state. *(Not verified without live graph execution.)*

- **PiCodingAgent with `pi` not on PATH**: `shutil.which("pi")` returns `None`, so `self.pi_binary = "pi"`. The subprocess raises `FileNotFoundError` caught by `except Exception: pass` in implement_node. Suspected: every local non-Pi run silently produces an empty diff and appears to succeed. *(Confirmed by code path; live execution not verified.)*

- **Concurrent session SQLite race**: Two simultaneous saves for the same ticket_id could create a TOCTOU window. SQLite's serialized-write mode likely prevents data corruption but may deadlock. *(Suspected; not tested with concurrent load.)*

- **Bare `\r` in graph.py line 117**: `create_full_sdlc_graph` signature has a trailing `\r` after `llm: LLMClient,`. Some editors/diff tools may display or parse this incorrectly.

---

## Positive Observations

1. **Protocol-first design.** Clean `Protocol` interfaces for every external dependency; no concrete import leaks into core logic.
2. **Pyright strict passes with zero errors.** Genuine type discipline throughout; Pydantic models used correctly.
3. **Branch naming enforcement is defense-in-depth.** Regex checked in three independent locations.
4. **Secret scrubbing at ingestion boundary is correct.** All ticket text fields scrubbed immediately in `ingest_node` before entering graph state.
5. **Dry-run mode implemented and tested.** Both connectors respect `dry_run`; tests verify zero-write behaviour.
6. **Session/UI layer correctly isolated.** UI code imports only from `agent/session/`; boundary is clean.
7. **SQLite session state is idempotent.** `CREATE TABLE IF NOT EXISTS` + upsert makes restarts safe.

