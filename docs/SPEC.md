# SPEC.md

Requirements for the Azure DevOps SDLC agent. Design lives in `docs/ARCHITECTURE.md`; working rules for coding agents live in `AGENTS.md`.

## Goal

- Build a real Azure DevOps SDLC agent: ticket in, draft PR out.
- It must work end to end and be measurable, for use as a portfolio project.

## Workflow

1. **Ingest:** pull the work item via the ADO REST API, including description, acceptance criteria, comments and linked items.
2. **Clarify:** score the ticket against a rubric and generate 3-5 questions. Check ticket comments for existing answers. If answers are present in comments, absorb them directly; for any questions that remain unanswered, queue them in the ticket's local session and pause. The user sees them when they open the session, answers them there, and the run resumes. (Later, as an optional channel: post unanswered questions as an ADO comment, tag the ticket `needs-clarification`, and resume when a reply arrives.)
3. **Impact analysis:** use Codegraph to find callers, usages and covering tests. Propose 2-3 solutions, score blast radius (files touched, API/schema changes, shared modules, test coverage), pick the smallest, and get approval.
4. **Tests first:** generate unit tests and a Playwright spec from the acceptance criteria, and confirm they fail for the right reason.
5. **Implement:** work in an isolated git worktree on a branch named `agent/<id>-slug`, with a file allowlist, diff-size cap and iteration cap. Coding agent (Pi) runs via CLI.
6. **Verify locally:** build, lint, new tests, impacted existing tests, then Playwright against the running app with traces and screenshots. A scope guard fails the run if the diff leaves the approved plan.
7. **Raise the PR:** open a draft via the internal ADO connector (`PRHost.create_draft_pr` linked to work items), with the plan, blast-radius reasoning, tests, evidence and limitations. It never merges or pushes to main.

## Stack and guardrails

- LangGraph state machine with human-approval interrupts (after the plan and before the PR), plus LangSmith tracing.
- Least-privilege PAT, tests in Podman, dry-run mode (local worktree/test execution permitted, zero remote writes or pushes), and no secrets in model context.
- Built on a free ADO org with a sample repo (.NET + React), not employer tickets or repos.
- Inference through an OpenCode Go subscription only; no other provider keys. Pi is the coding agent (invoked via CLI), and our agent uses internal tools and connectors. LSPs provide syntax and type diagnostics in the inner loop.
- Scope for v1: C#, JavaScript (React), Azure DevOps and Playwright only. The design stays open to additional stacks through adapter interfaces.

## Human interaction & project management

- Humans interact through sessions, one per ticket. The run asks for input (clarification answers, plan approval, PR approval) and waits.
- Local project management runs from the repository root, maintaining `.agent/` (ignored by git):
  - `.agent/sessions.sqlite`: Persistent checkpoint storage and ticket registry across CLI restarts.
  - Ticket and branch registry: tracks active/completed tickets, associated feature branches (`agent/<id>-<slug>`), worktree paths, statuses, and PR links.
  - CLI project dashboard (`agent status`, `agent list`, `agent attach <id>`, `agent clean [id]`): displays table of active tickets in flight, pending questions/approvals, and branch statuses.
- v1 uses a local CLI (Typer + Rich), with a TUI later. ADO comments are an optional later channel.
- Evals use an automatic answerer so runs are unattended.

## Evals

- Build an eval set from tickets that have merged fixes: reset to the commit before the fix, run the agent, and compare its diff to the real one.
- The free org has no history, so the tickets and their fixing PRs are authored against the sample app.
- Track clarification rate, first-pass test success, iterations, time, blast-radius size, and human edits to the PR.
