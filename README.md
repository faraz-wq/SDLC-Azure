# Azure DevOps SDLC Agent

An autonomous, guardrailed software delivery lifecycle agent for Azure DevOps: **Work item in, draft pull request out.**

Built as a deterministic **LangGraph state machine** with human-in-the-loop approval gates, strict least-privilege isolation, blast radius scoring, and offline benchmark evaluations.

---

## Architecture & Lifecycle

The agent executes a structured, multi-stage state machine designed to minimize human toil while enforcing strict engineering guardrails:

```
[Azure DevOps Work Item]
         │
         ▼
     [Ingest] ───────────────► Ingest description, acceptance criteria, linked items
         │
         ▼
  [Clarify Score] ───────────► Evaluates spec clarity against a YAML rubric
         │
         ├─► (Score < 8.0) ──► [Post Questions] ──► [Human Approval Gate] ──► (Resume)
         │
         ▼
  [Impact Analysis] ─────────► Analyzes affected symbols, callers, and test targets
         │
         ▼
  [Propose Options] ─────────► Generates 2–3 architectural options (files touched, API changes)
         │
         ▼
   [Blast Score] ────────────► Calculates blast radius score
         │
         ▼
  [Select Smallest] ─────────► Chooses the option with the minimal blast radius
         │
         ▼
  [Approve Plan] ────────────► [Human Approval Gate: Plan Frozen]
         │
         ▼
   [Write Tests] ────────────► Generates unit & integration tests
         │
         ▼
   [Confirm Red] ────────────► Verifies tests fail before implementation begins
         │
         ▼
    [Implement] ─────────────► Modifies code inside an isolated git worktree
         ▲
         │ (Loop capped)
         ▼
     [Verify] ───────────────► Runs sandboxed test suite & enforces Scope Guard
         │
         ▼
   [Approve PR] ─────────────► [Human Approval Gate: Review Diff & Verification Evidence]
         │
         ▼
  [Raise Draft PR] ──────────► Pushes branch `agent/<id>-<slug>` & creates Draft PR in ADO
```

---

## Safety Guardrails (Zero-Compromise Policy)

1. **Least-Privilege Branching**:
   - The agent **never** pushes directly to `main` and **never** merges pull requests.
   - All code is committed to strictly isolated branches matching `agent/<ticket-id>-<slug>`.
   - Pull requests are always created as **Draft PRs**.
2. **Scope Guard**:
   - Strictly enforces the frozen plan's `allowed_files`. Any file touched outside the allowlist immediately aborts the run.
   - Path-traversal and prefix-bypass resistant.
3. **Diff & Iteration Caps**:
   - Caps diff size to 300 lines by default (`max_diff_lines`).
   - Caps implement-verify inner loops to 5 iterations max (`max_iterations`).
4. **Secret Scrubbing**:
   - All text leaving or entering the agent is scrubbed for Personal Access Tokens (PATs), connection strings, and API keys.

---

## Prerequisites & Installation

- **Python 3.12+**
- [`uv`](https://github.com/astral-sh/uv) (recommended package manager)

```bash
# Clone the repository
git clone https://github.com/your-username/SDLC-Azure.git
cd SDLC-Azure

# Install dependencies and setup environment
uv sync
```

---

## Configuration

Create a `.env` file in the repository root:

```ini
# Azure DevOps Configuration
AZURE_DEVOPS_ORG=your-ado-organization
AZURE_DEVOPS_PROJECT=your-project-name
AZURE_DEVOPS_REPO=your-repo-name
AZURE_DEVOPS_PAT=your-personal-access-token

# Inference LLM API Key (OpenCode / LLM Client)
OPENCODE_API_KEY=your-api-key
```

---

## Usage

### 1. Interactive Terminal REPL

Launch the interactive coding terminal:

```bash
uv run agent chat
```

Features:
- Type `/` to open an interactive command popup with live counts (`Commands [1/8]`) and arrow-key navigation.
- Inline slash commands:
  - `/ado`: Inspect Azure DevOps connection status.
  - `/run <id>`: Run SDLC pipeline on a specific work item.
  - `/run <id> --dry-run`: Run safely with zero writes to remote ADO.
  - `/status`: View active ticket sessions and worktrees.
  - `/clean <id>`: Prune local session artifacts and delete temporary worktrees.
  - `/help`: Show command documentation.

### 2. Non-Interactive CLI

Run directly from your terminal or CI/CD pipelines:

```bash
# Check status in human-readable table or structured JSON
uv run agent status
uv run agent status --json

# Run a ticket in safe dry-run mode (local worktree, sandboxed tests, 0 ADO writes)
uv run agent run 101 --dry-run --yes

# Run live ticket execution
uv run agent run 101 --yes

# Attach to an existing session waiting on human approval
uv run agent attach 101

# Clean a completed ticket session
uv run agent clean 101 --yes
```

---

## Benchmark Evaluation Suite

The repository includes a benchmark test harness (`evals/`) evaluating the agent across 12 realistic work item archetypes:

- **Archetype A**: Localized UI & Behavior Fixes (small diffs, zero clarification needed).
- **Archetype B**: Vague / Under-specified Tickets (verifies rubric scoring, question generation, and human pause).
- **Archetype C**: API & Backend Contract Changes (DTO updates, validation codes, idempotency).
- **Archetype D**: Cross-Cutting & Domain Rules (nullable joins, enum migrations, blast radius).

### Run the Benchmark

```bash
# Execute evaluation suite
uv run python -m evals.runner

# Export metrics to JSON
uv run python -m evals.runner --json eval_report.json
```

**Benchmark Results:**
```text
                          Benchmark Evaluation Results                          
┏━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃    ID ┃ Archetype   ┃ Clarified? ┃ Rubric Match ┃ Draft PR? ┃  Time ┃ Result ┃
┡━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│  4966 │ localized_… │     NO     │      ✔       │     ✔     │ 0.10s │  PASS  │
│  4952 │ localized_… │     NO     │      ✔       │     ✔     │ 0.09s │  PASS  │
│  5001 │ localized_… │     NO     │      ✔       │     ✔     │ 0.09s │  PASS  │
│  4969 │ vague_spec  │    YES     │      ✔       │     ✔     │ 0.09s │  PASS  │
│ 11619 │ vague_spec  │    YES     │      ✔       │     ✔     │ 0.09s │  PASS  │
│ 10922 │ vague_spec  │    YES     │      ✔       │     ✔     │ 0.09s │  PASS  │
│ 11595 │ api_contra… │     NO     │      ✔       │     ✔     │ 0.08s │  PASS  │
│ 10923 │ api_contra… │     NO     │      ✔       │     ✔     │ 0.08s │  PASS  │
│ 10943 │ api_contra… │     NO     │      ✔       │     ✔     │ 0.08s │  PASS  │
│ 11680 │ cross_cutt… │     NO     │      ✔       │     ✔     │ 0.08s │  PASS  │
│ 11620 │ cross_cutt… │     NO     │      ✔       │     ✔     │ 0.08s │  PASS  │
│  5011 │ cross_cutt… │     NO     │      ✔       │     ✔     │ 0.08s │  PASS  │
└───────┴─────────────┴────────────┴──────────────┴───────────┴───────┴────────┘

Summary:
- Overall Pass Rate: 100.0% (12/12)
- Clarification Rubric Accuracy: 100.0% (12/12)
```

---

## Development & Quality Gates

The codebase strictly adheres to type safety, formatting, and test quality gates:

```bash
# Run unit & integration test suite (41 tests)
uv run pytest -q

# Format check & lint check
uv run ruff check . && uv run ruff format --check .

# Strict typechecking
uv run pyright
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
