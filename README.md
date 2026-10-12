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
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip` / `pipx`

### 1. Global Installation (Recommended)

Install globally on any system to get the `agent` command in your terminal:

**Using `uv` (Fastest, Cross-Platform):**
```bash
uv tool install git+https://github.com/faraz-wq/SDLC-Azure.git
```

**Using `pip` / `pipx`:**
```bash
pipx install git+https://github.com/faraz-wq/SDLC-Azure.git
# or
pip install git+https://github.com/faraz-wq/SDLC-Azure.git
```

**From a Local Clone (macOS / Linux):**
```bash
git clone https://github.com/faraz-wq/SDLC-Azure.git
cd SDLC-Azure
./scripts/install.sh
```

**From a Local Clone (Windows PowerShell):**
```powershell
git clone https://github.com/faraz-wq/SDLC-Azure.git
cd SDLC-Azure
.\scripts\install.ps1
```

### 2. Uninstallation

**Using `uv` / `pipx` / `pip`:**
```bash
uv tool uninstall ado-sdlc-agent
# or
pipx uninstall ado-sdlc-agent
# or
pip uninstall -y ado-sdlc-agent
```

**Using Provided Scripts:**
- macOS / Linux: `./scripts/uninstall.sh`
- Windows PowerShell: `.\scripts\uninstall.ps1`

### 3. Local Development Setup

```bash
git clone https://github.com/faraz-wq/SDLC-Azure.git
cd SDLC-Azure
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

### Benchmark Execution

```bash
# Execute evaluation suite (offline deterministic mode)
uv run python -m evals.runner

# Execute evaluation suite against live LLM API
uv run python -m evals.runner --live

# Export metrics to JSON
uv run python -m evals.runner --json eval_report.json
```

### Benchmark Results & Metrics

#### 1. Evaluation Scorecard

| Case ID | Archetype | Work Item Summary | Clarification? | Rubric Accuracy | Draft PR Created | Status |
|:---:|:---|:---|:---:|:---:|:---:|:---:|
| **SDLC-101** | Localized UI Bug | App Header and Navigation Remain Fixed | NO | 100% | YES (`agent/4966-...`) | **PASS** |
| **SDLC-102** | Localized UI Bug | Indicate Updated Solutions with 'New' Tag | NO | 100% | YES (`agent/4952-...`) | **PASS** |
| **SDLC-103** | Localized UI Bug | Benefits Widget Progress Bar Zero Division | NO | 100% | YES (`agent/5001-...`) | **PASS** |
| **SDLC-201** | Vague Specification | Update Login Error Message for Inactive Accounts | **YES** (Paused) | 100% | YES (`agent/4969-...`) | **PASS** |
| **SDLC-202** | Vague Specification | Resolve Missing Chat Email Destination Handling | **YES** (Paused) | 100% | YES (`agent/11619-...`) | **PASS** |
| **SDLC-203** | Vague Specification | Telephony Voicemail Failure in Test Env | **YES** (Paused) | 100% | YES (`agent/10922-...`) | **PASS** |
| **SDLC-301** | API Contract Change | Return HTTP 422 for Invalid Contact Format | NO | 100% | YES (`agent/11595-...`) | **PASS** |
| **SDLC-302** | API Contract Change | Deduplicate Rapid Clicks on Activity Save | NO | 100% | YES (`agent/10923-...`) | **PASS** |
| **SDLC-303** | API Contract Change | Suppress Background SMS for Restricted Cohort | NO | 100% | YES (`agent/10943-...`) | **PASS** |
| **SDLC-401** | Cross-Cutting Domain | Assessment Order Care Need Sync to Care Plan | NO | 100% | YES (`agent/11680-...`) | **PASS** |
| **SDLC-402** | Cross-Cutting Domain | Nullable Join for Blank Coverage Records | NO | 100% | YES (`agent/11620-...`) | **PASS** |
| **SDLC-403** | Cross-Cutting Domain | Enum Migration for Solution Need Subcategories | NO | 100% | YES (`agent/5011-...`) | **PASS** |

#### 2. Key Performance Indicators

- **Overall Pass Rate**: `100.0%` (12 / 12 benchmark cases passed)
- **Clarification Rubric Accuracy**: `100.0%` (12 / 12)
  - **Precision**: 0 false positives (never halted for questions on well-specified tickets).
  - **Recall**: 0 false negatives (100% detection of missing acceptance criteria & ambiguous specs).
- **Scope Guard Compliance**: `100%` (zero violations outside `allowed_files`).
- **Diff Cap Adherence**: All diffs strictly contained within the `300` max line limit.
- **Least-Privilege Enforcement**: Zero direct pushes to `main`; 100% Draft PR generation on isolated feature branches.

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
