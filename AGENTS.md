# AGENTS.md

Rules for any AI coding agent working on this repository. Read this file and `docs/ARCHITECTURE.md` before every task.

## Project

An Azure DevOps SDLC agent: work item in, draft pull request out. It is built as a LangGraph state machine with human-approval interrupts, and it must be end-to-end functional and measurable (see Evals in `docs/ARCHITECTURE.md`).

This is a portfolio project. It runs only against the sample org and sample repo (.NET + React), never against employer tickets or repositories.

## How to work

1. **One slice per session.** Do the slice you were given and nothing else. If you spot unrelated work, list it at the end of your reply and do not do it.
2. **Plan first.** Before writing code, state the files you will create or change and the interfaces involved. Wait for approval on anything that changes a protocol or schema in `agent/core/`.
3. **Tests first.** For every new node, tool or guard, write the failing test, show it failing for the right reason, then implement.
4. **Fakes before real services.** Develop against `FakeTicketSource`, `FakePRHost`, `FakeCodingAgent` and `FakeStackAdapter`. Real ADO, Pi and Podman integrations come only when a slice says so.
5. **Small diffs.** Prefer many small, reviewable changes. Do not reformat or rename files you are not otherwise changing.
6. **Stop and ask** when the spec is ambiguous, when a requirement conflicts with another, or when you would need to weaken a guardrail to proceed.

## Commands

```
uv sync                     # install
uv run pytest -q            # all tests
uv run pytest -q -m "not integration"   # fast, offline tests
uv run ruff check . && uv run ruff format --check .
uv run pyright              # strict mode must pass
```

A slice is done only when tests, ruff and pyright all pass.

## Code conventions

- Python 3.12, `uv`, pytest, ruff, pyright (strict).
- All graph state and all data crossing a module boundary is a typed pydantic model defined in `agent/core/schemas.py` and `agent/core/state.py`. No raw dicts between nodes; nodes return typed updates conforming to `RunState`.
- Nodes are pure-ish functions: `(state, deps) -> state update`. External access goes through injected interfaces, never imported clients.
- Core code (`agent/core/`, `agent/nodes/`, `agent/guards/`) must not mention a specific language, framework, host or coding agent. Those live in `agent/adapters/`, `agent/verifiers/`, `agent/connectors/` and `agent/coding/`.
- UI code (`agent/ui/`) talks only to `agent/session/`. It never imports nodes, adapters or connectors.
- Log structured events with the run id and node name. Never log secrets, tokens or full environment dumps.
- Every external call has a timeout. Every loop has a hard iteration cap from config.

## Hard rules (never violate)

- Never push to `main`, merge a PR, or approve a PR. The agent only creates **draft** PRs from branches named `agent/<id>-<slug>`.
- Never place secrets (PAT, API keys, connection strings) in prompts, state, traces, logs, test fixtures or committed files. Secrets come from the environment and are read only inside the connector that needs them. Run all outbound text through `guards/secret_scrub.py`.
- Never run generated or modified code outside the Podman sandbox (no network, no mounted secrets, resource limits).
- Never edit files outside the approved plan's `allowed_files`. The scope guard enforces this and must not be bypassed, loosened or silenced in order to make a run pass.
- Never delete or weaken a failing test to make it pass. Fix the code or report the problem.
- Never use `--force`, `reset --hard` on shared branches, or any history rewrite outside an agent-owned worktree.
- Dry-run mode allows local worktree creation, code generation, and sandboxed test execution, but must perform zero writes to ADO (no PRs, tags, or comments) and zero remote pushes. Test this explicitly.

## Review-critical files

The following files carry the safety story. Keep them small, readable and fully tested. Flag any change to them clearly in your summary so a human reviews them line by line:

- `agent/guards/scope_guard.py`
- `agent/guards/diff_cap.py`
- `agent/guards/iteration_cap.py`
- `agent/guards/secret_scrub.py`
- `agent/tools/git_worktree.py`
- `agent/connectors/pr_host_azure.py`

## Definition of done for a slice

- [ ] Behavior matches `docs/SPEC.md` and `docs/ARCHITECTURE.md`
- [ ] Tests added, including at least one failure-path test
- [ ] `pytest`, `ruff`, `pyright` pass
- [ ] No new dependency without a one-line justification in the PR description
- [ ] `docs/` updated if an interface or schema changed
- [ ] Summary lists: files changed, decisions made, anything deferred

## Out of scope for v1

Integrations beyond C#, JavaScript/TypeScript, Playwright and Azure DevOps. Design for extension through the adapter interfaces, but do not write adapters for other stacks.
