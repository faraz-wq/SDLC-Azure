# Remediation Roadmap

Priority order within each tier: highest severity first, then quickest fix.

---

## (a) Fix Now — Blockers (before any "live" demo or portfolio review)

These must be resolved before the agent touches a real ADO org or before the repo
is shared with anyone evaluating the security posture.

| # | ID | Fix | Effort | Depends on |
|---|---|---|---|---|
| 1 | **SEC-001** | Remove substring fallback from `check_scope`; anchor allowed-file matching to path boundaries | S | — |
| 2 | **SEC-002** | Fixed automatically by SEC-001 fix | S | SEC-001 |
| 3 | **CODE-001** | `implement_node`: replace bare `except Exception: pass` with typed catch + state.error set | S | ARCH-003 (failure terminal) |
| 4 | **CODE-008** | Add `timeout=` to `urlopen` in `OpenCodeClient.complete()` | S | — |
| 5 | **CODE-009** | Add `timeout=` to all urlopen calls in both connectors | S | — |

**Exact fix for SEC-001** (`agent/guards/scope_guard.py` line 42):
```python
# Replace:
if fnmatch.fnmatch(norm_file, clean_allowed) or clean_allowed in norm_file:
# With:
boundary_match = (
    norm_file == clean_allowed
    or norm_file.startswith(clean_allowed.rstrip("/") + "/")
)
if fnmatch.fnmatch(norm_file, clean_allowed) or boundary_match:
```
Then add the two adversarial tests from `audit/scratch/test_adversarial.py` to `tests/test_scope_guard.py`.

---

## (b) Next Sprint — Correctness and Reliability

Address before end-to-end testing against live ADO.

| # | ID | Fix | Effort | Depends on |
|---|---|---|---|---|
| 6 | **ARCH-003** | Add failure terminal node; conditional error edges from every node | M | — |
| 7 | **SEC-004** | Implement `push_branch` via subprocess git push | M | — |
| 8 | **DEVOPS-001** | Add `.github/workflows/ci.yml` | S | — |
| 9 | **CODE-003** | On LLM parse failure in `clarify_score_node`, log warning + force clarification (score=0) | S | — |
| 10 | **CODE-004** | `propose_options_node`: log + set state.error instead of bare pass | S | ARCH-003 |
| 11 | **CODE-007** | `OpenCodeClient`: handle null content (reasoning-model), retry on length, record reasoning_tokens | M | — |
| 12 | **ARCH-004** | Source `max_diff_lines` from `AgentConfig` in `select_smallest_node` | S | — |
| 13 | **SEC-003** | Expand env-var scrubbing to cover `*_KEY`, `*_SECRET`, `*_TOKEN`, `*_PAT`, `*_PASSWORD` patterns | M | — |

---

## (c) Structural Refactors — Next 2-3 Slices

These require more design thought or are gated on other slices completing first.

| # | ID | Fix | Effort | Depends on |
|---|---|---|---|---|
| 14 | **ARCH-001** | Implement the four stub nodes properly (StackAdapter, Verifier injected) | L | SEC-004, ARCH-003 |
| 15 | **ARCH-002** | Migrate node deps from closures to LangGraph RunnableConfig.configurable | M | ARCH-001 |
| 16 | **CODE-010** | Switch `RunState.messages` to LangGraph `add_messages` reducer | S | — |
| 17 | **CODE-002** | Normalise line endings; add `.gitattributes` | S | — |

---

## (d) Backlog — Polish and Nice-to-Haves

| # | ID | Fix | Effort |
|---|---|---|---|
| 18 | **CODE-005** | Rewrite `set_tag` to PATCH only the tags field | S |
| 19 | **CODE-006** | Use comment integer ID as marker in `new_replies_since` | S |
| 20 | **DOCS-001** | Add implementation status checklist to README.md | S |
| 21 | **UX-001** | Run graph in background thread; stream Rich Live progress events | M |
| 22 | **UX-002** | Surface TUI answer-collection failures as visible notifications | S |

---

## Quick Wins (High Impact / Low Effort)

These can all be done in a single focused session:

1. **SEC-001 + SEC-002**: One-line change in scope_guard + 2 new tests (~30 min)
2. **CODE-008 + CODE-009**: Add `timeout=` in 7 urlopen calls (~15 min)
3. **DEVOPS-001**: Basic CI YAML file (~20 min)
4. **CODE-003 + CODE-004**: Replace two bare `except: pass` blocks with logs/errors (~20 min)
5. **ARCH-004**: Replace `max_diff_lines=150` hardcode (~5 min)

**Total estimated time for quick wins: ~90 minutes.** These address 2 Critical and 3 High findings.

---

## Dependency Graph

```
SEC-001 ──► SEC-002 (auto-fixed)
CODE-001 ──► ARCH-003 (need failure terminal first)
ARCH-003 ──► CODE-004, CODE-001 (proper error routing)
SEC-004 ──► ARCH-001 (push needed for real PR)
ARCH-001 ──► ARCH-002 (refactor after nodes are real)
DEVOPS-001 ─ (independent, do immediately)
```

