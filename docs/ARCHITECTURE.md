# ARCHITECTURE.md

Design for the Azure DevOps SDLC agent. Companion to `docs/SPEC.md` (the workflow and guardrail requirements) and `AGENTS.md` (working rules).

## 1. Goals and non-goals

**Goals**
- Ticket in, draft PR out, end to end, on a sample .NET + React repo in a free ADO org.
- Safe by construction: guardrails are enforced in code and infrastructure, not by prompting.
- Measurable: every run emits metrics that the eval harness aggregates.
- Extensible: new stacks, hosts and coding agents plug in without editing graph code.

**Non-goals (v1)**
- Merging, approving or pushing to protected branches.
- Stacks other than C#, JS/TS and Playwright. Hosts other than Azure DevOps.
- Working on employer tickets or repositories.

## 2. System overview

A single LangGraph state machine with a persistent checkpointer (SQLite for dev). Runs can pause for days (clarification, approvals), so all state must survive a process restart.

```
ingest
  -> clarify_score --(sufficient)--------------------------+
        |                                                   |
        +--(gaps)--> post_questions -> INTERRUPT:await_reply -> ingest
                                                            |
                                                            v
  impact_analysis -> propose_options -> blast_score -> select_smallest
  -> INTERRUPT:approve_plan
  -> write_tests -> confirm_red
  -> implement <-> verify        (bounded loop, iteration cap)
  -> scope_guard
  -> INTERRUPT:approve_pr
  -> raise_draft_pr -> done
```

Failure exits: any node may route to `abort`, which records the reason, comments on the ticket if allowed, cleans up the worktree and ends the run. Dry-run mode follows the same path but replaces every write with a logged no-op.

## 3. Package layout

```
agent/
  core/
    state.py            # RunState (pydantic), reducers
    schemas.py          # Ticket, Plan, Option, BlastRadius, TestReport, StepResult, Diagnostic, RunMetrics
    protocols.py        # TicketSource, PRHost, StackAdapter, Verifier, CodingAgent, CodeIndex
    config.py           # caps, thresholds, paths, feature flags
    registry.py         # adapter discovery and detection
  graph.py              # wiring only: nodes, edges, interrupts, checkpointer
  nodes/                # one file per node; no stack- or vendor-specific code
  guards/               # scope_guard, diff_cap, secret_scrub, iteration_cap
  tools/                # git_worktree, container_runner, diff_utils
  adapters/             # csharp/, javascript/   (StackAdapter implementations)
  verifiers/            # playwright/            (Verifier implementation)
  connectors/           # ticket_source_azure, pr_host_azure
  coding/               # pi_agent (CodingAgent), fake_agent
  llm/                  # LLMClient implementations (opencode_go, fake), models.yaml loader
  channels/             # HumanChannel: local_session (v1), auto_answer (evals), ado_comment (later)
  session/              # session API over the checkpointer: list, get_pending, submit_response
  ui/                   # cli/ (Typer + Rich) now, tui/ (Textual) later; import only session/
  rubric/               # ticket_rubric.yaml, scorer
  obs/                  # LangSmith tracing, metrics emitters
evals/
  build_dataset.py  run_eval.py  metrics.py  report.py  datasets/
sample-app/             # .NET API + React frontend + seeded tickets
tests/
docs/
```

The rule that keeps this extensible: `core/`, `nodes/` and `guards/` import only from `core/`. Concrete implementations are injected at graph construction.

## 4. Core interfaces

```python
class TicketSource(Protocol):
    def get_ticket(
        self, id: int
    ) -> Ticket: ...  # description, acceptance criteria, comments, linked items
    def post_comment(self, id: int, body: str) -> None: ...
    def set_tag(self, id: int, tag: str, present: bool) -> None: ...
    def new_replies_since(self, id: int, marker: str) -> list[Comment]: ...


class PRHost(Protocol):
    def create_draft_pr(self, branch: str, title: str, body: str, work_item: int) -> PRRef: ...
    def push_branch(
        self, branch: str
    ) -> None: ...  # refuses anything not matching agent/<id>-<slug>


class StackAdapter(Protocol):
    name: str

    def detect(self, repo: Path) -> bool: ...
    def index(self, repo: Path) -> CodeIndex: ...  # callers, usages, covering tests
    def lsp_config(self) -> LspServer: ...  # inner-loop diagnostics
    def build(self, wt: Path) -> StepResult: ...
    def lint(self, wt: Path) -> StepResult: ...
    def run_tests(self, wt: Path, targets: list[str]) -> TestReport: ...
    def classify_failure(self, report: TestReport) -> FailureKind: ...
    def test_scaffold(self) -> TestTemplates: ...
    def risk_rules(self) -> list[RiskRule]: ...


class Verifier(Protocol):  # e.g. Playwright
    def prepare(self, wt: Path) -> AppHandle: ...  # start the app under test
    def generate_spec(self, criteria: list[str], plan: Plan) -> list[Path]: ...
    def run(self, app: AppHandle, specs: list[Path]) -> VerifierReport: ...  # traces, screenshots


class CodingAgent(Protocol):
    def run(
        self, task: CodingTask, wt: Path, limits: Limits
    ) -> CodingResult: ...  # iterations, tokens, final diff


class LLMClient(Protocol):  # used by graph nodes (clarify, plan, PR text, judge)
    def complete(
        self,
        role: ModelRole,
        messages: list[Message],
        *,
        schema: type[BaseModel] | None = None,
        max_output_tokens: int,
        session_id: str,
    ) -> LLMResult: ...

    # LLMResult: text, parsed (if schema), finish_reason, usage (input, output, reasoning, cached), model_id


class HumanChannel(Protocol):  # how the run asks a human and gets answers
    def ask(self, session_id: str, request: HumanRequest) -> None: ...  # queue it
    def collect(self, session_id: str) -> HumanResponse | None: ...  # answer if present


# HumanRequest variants: Questions (3-5 clarifications), PlanApproval, PRApproval
```

All data crossing these boundaries uses the normalized types in `schemas.py`, so metrics and the PR body are stack-agnostic.

## 5. Node responsibilities

| Node | Input | Output | Notes |
|---|---|---|---|
| ingest | ticket id | `Ticket` | Description, acceptance criteria, comments, linked items. Scrub before model context. |
| clarify_score | `Ticket` | rubric scores, questions | Rubric lives in YAML; checks comments for existing answers. Absorbs answered items; produces remaining unanswered questions. |
| post_questions | questions | `Questions` request queued on the `HumanChannel` | Then interrupt. Unanswered questions await human input in local session. On resume, answers merge into state; re-score. |
| impact_analysis | `Ticket`, merged `CodeIndex` | affected symbols, callers, covering tests | Merge indexes from all active adapters; model API routes as explicit nodes joining C# and JS. |
| propose_options | impact | 2-3 `Option`s | Each lists files touched and API or schema changes. |
| blast_score | `Option`s | `BlastRadius` per option | Weighted: files touched, public API or schema change, shared-module hits, uncovered-caller ratio. Log components, not only the total. |
| select_smallest | scores | `Plan` | Contains `allowed_files`, `max_diff_lines`, `expected_api_changes`, `test_targets`. |
| approve_plan | `Plan` | decision | Human interrupt. Plan is frozen after approval. |
| write_tests | criteria, plan | unit tests and Playwright spec | Via `CodingAgent` and `test_scaffold`. |
| confirm_red | tests | pass or abort | Tests must fail with an assertion tied to the feature, not a compile error or missing import. Classified by the adapter. |
| implement | plan | diff | Runs in worktree `agent/<id>-<slug>`. Limits: allowlist, diff cap, iteration cap. Coding agent (Pi) runs via CLI. LSP diagnostics feed the inner loop. |
| verify | worktree | `VerifyReport` | Build, lint, new tests, impacted existing tests, then Playwright with traces and screenshots. All in Podman. |
| scope_guard | diff, plan | pass or fail | Fails the run if any file is outside `allowed_files`, the diff exceeds the cap, or unplanned API or schema changes appear. |
| approve_pr | PR draft | decision | Human interrupt. |
| raise_draft_pr | PR draft | `PRRef` | ADO REST API in `pr_host_azure.py` (`create_draft_pr` with work item link). Body: plan, blast-radius reasoning, tests, evidence, limitations. |

## 6. The Plan object

The approved plan is the contract for everything downstream.

```python
class Plan(BaseModel):
    ticket_id: int
    summary: str
    chosen_option: Option
    rejected_options: list[Option]  # with reasons, for the PR body
    blast: BlastRadius
    allowed_files: list[str]  # globs, exact where possible
    max_diff_lines: int
    expected_api_changes: list[str]
    test_targets: list[str]
    approved_by: str | None
    approved_at: datetime | None
```

`scope_guard`, the coding agent's task prompt and the PR description all read from this one object.

## 7. Guardrails and where they are enforced

| Guardrail | Enforcement point |
|---|---|
| Never push to or merge into `main` | ADO branch policy on `main` (PR required, no direct push). `PRHost.push_branch` also refuses non-`agent/<id>-<slug>` refs. |
| Least-privilege PAT | Scopes: Work Items (Read and Write), Code (Read and Write). Stored in env only; read inside connectors only. |
| No secrets in model context | `guards/secret_scrub.py` runs on all text entering prompts, traces and logs. Tests include seeded fake secrets. |
| Sandboxed execution | `tools/container_runner.py`: no network, no secret mounts, CPU, memory and time limits. |
| Stay inside the plan | `guards/scope_guard.py` post-checks `git diff` against `Plan`. Never relies on the model obeying a prompt. |
| Bounded effort | `guards/diff_cap.py` and `guards/iteration_cap.py`, values from config. |
| Dry-run | A single `dry_run` flag in config. Local git worktree creation, code generation, and sandboxed test execution run normally; remote write operations in connectors (`push_branch`, `create_draft_pr`, `post_comment`, `set_tag`) return logged no-ops. Test asserts zero remote writes. |
| Human oversight | Interrupts after plan and before PR. Not skippable in code paths. |

## 8. Adapters and extensibility

- **Registration:** adapters register through entry points and a config list. `detect(repo)` decides which are active; mixed repos use several at once.
- **v1 implementations:** `csharp` (Roslyn index, `dotnet build`, xUnit, OmniSharp or csharp-ls), `javascript` (TS compiler API or tree-sitter index, tsserver, eslint, Vite + Vitest), `playwright` (verifier), `azure_devops` (ticket source and PR host).
- **Extension claim, and its test:** adding a new stack touches no file in `core/`, `nodes/` or `guards/`. A stub adapter in `tests/` is loaded through the registry to prove it.
- **Speculative adapters are not built.** Interfaces grow only when a real adapter needs them.

## 9. Observability

- LangSmith tracing on every graph run, tagged with run id, ticket id, adapter set and coding agent.
- Each run emits a `RunMetrics` record: clarification asked (bool), questions count, first-pass test success, iterations, wall time, tokens, blast-radius components, diff size, guard failures, outcome.
- Metrics are written to a local JSONL file and linked from the PR body.

## 10. Evals

**Dataset.** The free org has no history, so authors write 15-25 realistic tickets against `sample-app/`, including: deliberately vague tickets, trivially small ones, ones needing a schema change, and ones touching shared modules. Each is fixed by a real PR that is merged, giving a pre-fix commit and a reference diff.

**Procedure.** For each ticket: check out the pre-fix commit into a fresh clone with future history stripped, run the agent with the ticket ingested but the original PR and linked fix excluded, with an `AutoAnswerer` channel handling every human request (section 14), and compare against the reference.

**Anti-leakage rules.** No future commits or refs in the clone. No access to the reference PR. Reference tests are hidden from the agent and used only for scoring.

**Metrics**

| Metric | Definition |
|---|---|
| Clarification rate | Share of runs that paused for questions; reported per rubric threshold, split by vague vs clear tickets |
| First-pass test success | New tests red-confirmed and then green without extra loops |
| Iterations | Implement/verify loops used |
| Time | Wall clock, per node and total |
| Blast-radius size | Predicted score vs actual diff size |
| Diff similarity | File-set precision and recall, hunk overlap |
| Reference tests passing | Hidden reference tests run against the agent's change (strongest signal) |
| Human edits to PR | Line delta between draft PR and the version a human merges |

Run each ticket 3 times and report variance. `evals/report.py` produces a markdown summary with a per-ticket table and aggregate charts.

## 11. Build order (vertical slices)

0. Skeleton: repo, CI, a two-node graph with checkpointing.
1. Protocols, schemas and fakes.
2. ADO ingest against the real sample org, plus recorded-fixture tests.
3. Clarify loop with interrupt and resume through the local session channel, plus a minimal CLI (`run`, `sessions`, `attach`).
4. Git worktree manager and dry-run mode.
5. Codegraph wrapper, impact analysis, plan object, plan approval.
6. Tests-first with confirm_red.
7. Implement/verify loop with caps, scope guard, Podman runner.
8. Playwright verifier and evidence.
9. Draft PR node and LangSmith tracing.
10. Eval harness (a minimal version should exist right after slice 5 so changes are measurable early).

Real Pi integration lands after the deterministic graph works with `FakeCodingAgent`.

## 12. Open decisions

- Codegraph backend: Roslyn for C# (decided). The demo frontend is React in plain JavaScript, so the JS index must work without TypeScript types: TS compiler API with `allowJs`, or tree-sitter. Both sit behind the `CodeIndex` interface..
- Resolved: SQLite checkpointer for local sessions. Postgres only if multi-process runs are needed.
- Resolved: replies are collected through the local session (section 14). Polling or an ADO webhook returns only if `AdoCommentChannel` is added.
- Pi's non-interactive or RPC mode and what telemetry (iterations, tokens) it exposes.
- Whether OpenCode permits unattended batch eval traffic from a custom client. The docs say Go is meant for OpenCode and similar coding agents; confirm before large runs.

## 13. LLM provider (OpenCode Go) and quota budget

Inference comes from one OpenCode Go subscription, with no other provider keys. Two consumers use it separately: Pi (implement and write-tests steps, configured in Pi's own provider settings) and graph nodes (through `LLMClient`).

**Connection**
- Base URL `https://opencode.ai/zen/go/v1`, key from `OPENCODE_API_KEY` (env only; read inside `llm/` only).
- Every request sends `User-Agent: ado-sdlc-agent/<version>` and `x-opencode-session: <run_id>` (stable per run, or per node conversation). Omitting the session header returns HTTP 400 `MissingSessionID`; treat that as a bug, not a retryable error.
- Transports: `chat_completions` first (GLM, Kimi, DeepSeek, MiMo, LongCat, Hy). `responses` (Grok, GPT Luna) and `messages` (MiniMax, Qwen) are added only when a role needs them.
- The `/v1/models` listing is inventory only. A startup health check makes a tiny real completion for each configured model.

**Reasoning-model handling (verified against glm-5.3-flash)**
- A response can have `content: null`, `finish_reason: "length"` and the model's thinking in `reasoning_content`, when the token budget is spent on reasoning.
- Rules: set `max_output_tokens` with generous headroom for reasoning; treat null content with `length` as a retryable budget-exhausted error (retry once with a larger budget); never use `reasoning_content` as the answer; record `reasoning_tokens` in `RunMetrics`.

**Roles in `models.yaml`** (initial values, to be tuned with evals)

```yaml
roles:
  clarify:   glm-5.3-flash      # rubric scoring and question generation
  plan:      deepseek-v4-pro    # options and blast-radius reasoning
  tests:     kimi-k2.7-code
  implement: kimi-k2.7-code     # via Pi
  judge:     glm-5.3-flash      # eval scoring helpers
denylist:
  - muse-spark-1.2-contributor  # trains on prompts
  - muse-spark-1.3-contributor
```

Config validation rejects denylisted models. Model IDs never appear in code.

**Errors:** retry 429 and 5xx with backoff and jitter; fail fast on 401 with a clear message; schema-validated outputs get one repair-and-retry before the node aborts.

**Quota budget**
- Limits are per model, with 5-hour (20%), weekly (50%) and monthly (100%) caps of that model's dollar limit. Cheaper models have far higher request counts than premium ones.
- `llm/` records usage from every response. The eval runner estimates budget before a batch, can resume, can run a subset, and caches deterministic node outputs.
- Plan for the weekly cap, not the monthly one. Prefer flash-tier models for high-volume roles.
- After a limit is hit, non-critical roles may fall back to a free model; implement and tests do not fall back silently.
- Unit tests and CI use `FakeLLMClient` only and never consume quota.

## 14. Sessions, Project Management, and the Human Channel

**Workspace Project Model (`.agent/`).**
The CLI treats the current working repository as the project root and manages local SDLC operations inside a `.agent/` directory (ignored by git):
```
.agent/
  sessions.sqlite     # SQLite checkpointer state and ticket/branch registry
  worktrees/          # isolated git worktrees per ticket: .agent/worktrees/<ticket-id>/
  logs/               # structured per-run execution logs
```

**Ticket & Branch Registry.**
The registry tracks all tickets in flight, their branch allocations, and lifecycle progress:

```python
class TicketRunRecord(BaseModel):
    ticket_id: int
    title: str
    branch_name: str                        # agent/<id>-<slug>
    worktree_path: str                      # .agent/worktrees/<id>
    status: SessionStatus                   # running, waiting_on_human, done, failed, aborted
    stage: str                              # ingest, clarify, plan, implement, verify, pr, complete
    pr_id: int | None = None
    pr_url: str | None = None
    pending_request: HumanRequest | None = None
    created_at: datetime
    updated_at: datetime
```

**Session & Project API** (in `agent/session/`, the only interface UIs import):

```python
get_project(repo: Path | None = None) -> ProjectContext
list_tickets() -> list[TicketRunRecord]                       # all tickets in flight/completed
get_pending(ticket_id: int) -> HumanRequest | None
submit_response(ticket_id: int, response: HumanResponse) -> None   # resumes the graph
clean_ticket(ticket_id: int, remove_worktree: bool = True) -> None # cleanup worktree/branch
```

Session statuses: `running`, `waiting_on_human`, `done`, `failed`, `aborted`.

**Requests**
- `Questions`: 3-5 clarification questions with the rubric gaps they address; the response is one answer per question (or "skip, make an assumption", which is recorded in the plan).
- `PlanApproval`: options, blast-radius components, chosen plan; the response is approve, reject with feedback, or pick a different option.
- `PRApproval`: diff summary, test results, evidence links, limitations; the response is approve or reject with feedback.

**Channels**
- `local_session` (v1): requests are stored in the session; the CLI or TUI reads and answers them.
- `auto_answer` (evals): answers clarification questions from a hidden full-detail version of each eval ticket, and auto-approves plans and PRs according to the eval config. Every auto-answer is logged in `RunMetrics` so clarification rate and answer quality can be audited.
- `ado_comment` (later): posts questions as ticket comments, sets `needs-clarification`, and resumes on a reply. Built on the existing `TicketSource` methods.

**UI plan.** Typer + Rich CLI first:
- `agent status` / `agent list`: Table view of all tickets, statuses, feature branches, worktrees, and pending approvals.
- `agent run <id>`: Ingests and starts/resumes work on a ticket.
- `agent attach <id>`: Connects to a running or paused ticket session.
- `agent approve <id>`: Submits human responses for pending clarification or plan/PR approvals.
- `agent clean [id]`: Cleans up local worktree and session artifacts.
Later, a Textual TUI with a session list and detail panes (questions form, plan view, diff viewer). Both are thin front ends over the session API. No UI library is imported by `core/`, `nodes/` or `session/`.
