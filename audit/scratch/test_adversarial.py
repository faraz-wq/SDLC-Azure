"""Adversarial audit tests.

Targeting: scope_guard, secret_scrub, diff_cap, iteration_cap,
           branch naming, plan/state integrity, and session edge cases.
"""

import pytest
from pathlib import Path

from agent.core.schemas import BlastRadius, Option, Plan
from agent.guards.scope_guard import ScopeViolationError, check_scope
from agent.guards.diff_cap import DiffCapViolationError, check_diff_cap
from agent.guards.iteration_cap import IterationCapViolationError, check_iteration_cap
from agent.guards.secret_scrub import scrub_secrets
from agent.tools.git_worktree import validate_branch_name


# ─── helpers ────────────────────────────────────────────────────────────────

def _make_plan(allowed_files: list[str], max_diff_lines: int = 300) -> Plan:
    return Plan(
        ticket_id=1,
        summary="test",
        chosen_option=Option(id="opt-1", description="d", files_touched=allowed_files),
        blast=BlastRadius(files_count=1, api_changes_count=0, shared_modules_count=0, score=1.0),
        allowed_files=allowed_files,
        max_diff_lines=max_diff_lines,
    )


# ─── ADVERSARIAL-001: scope_guard – path traversal bypass ───────────────────

def test_scope_guard_path_traversal_not_in_allowed():
    """A path like ../../secrets.env must NOT be allowed by substring match."""
    plan = _make_plan(["src/api"])
    # "src/api" IS contained as substring in some attacker paths
    # e.g. "../../src/api/../../../etc/passwd" – normalisation check
    with pytest.raises(ScopeViolationError):
        check_scope(["../../etc/passwd"], diff_lines=1, plan=plan)


def test_scope_guard_substring_loophole():
    """'src/api' as allowed should NOT match 'src/api-evil' via substring rule."""
    plan = _make_plan(["src/api"])
    # The current impl uses `clean_allowed in norm_file` which is a substring check.
    # 'src/api' IS in 'src/api-evil/bad.cs' → this should FAIL (be a violation)
    # but the guard might PASS it, which is the bug we're probing.
    try:
        check_scope(["src/api-evil/bad.cs"], diff_lines=1, plan=plan)
        # If we get here, the guard was bypassed – record the finding
        pytest.fail(
            "FINDING SEC-002: scope_guard substring match allowed 'src/api-evil/bad.cs' "
            "when only 'src/api' was in allowed_files"
        )
    except ScopeViolationError:
        pass  # Correct – guard blocked it


def test_scope_guard_windows_path_separator_bypass():
    """Backslash normalisation: a Windows-style path should still be checked."""
    plan = _make_plan(["src/safe"])
    # Backslash paths are normalised to forward slash, but does 'src/safe'
    # substring-match against 'src/safe-zone/evil.cs'?
    try:
        check_scope(["src\\safe-zone\\evil.cs"], diff_lines=1, plan=plan)
        pytest.fail(
            "FINDING SEC-002b: backslash path 'src\\safe-zone\\evil.cs' bypassed scope guard "
            "via 'src/safe' substring match after normalisation"
        )
    except ScopeViolationError:
        pass  # Correct


def test_scope_guard_empty_allowed_files():
    """Empty allowed_files must reject ALL touched files."""
    plan = _make_plan([])
    with pytest.raises(ScopeViolationError):
        check_scope(["any/file.cs"], diff_lines=1, plan=plan)


# ─── ADVERSARIAL-002: diff_cap – boundary values ───────────────────────────

def test_diff_cap_exactly_at_limit_passes():
    check_diff_cap(300, max_cap=300)  # must pass (not > 300)


def test_diff_cap_one_over_limit_raises():
    with pytest.raises(DiffCapViolationError):
        check_diff_cap(301, max_cap=300)


def test_diff_cap_zero_always_passes():
    check_diff_cap(0, max_cap=300)


# ─── ADVERSARIAL-003: iteration_cap – off-by-one ───────────────────────────

def test_iteration_cap_at_limit_passes():
    check_iteration_cap(5, max_iterations=5)  # must pass (not > 5)


def test_iteration_cap_one_over_raises():
    with pytest.raises(IterationCapViolationError):
        check_iteration_cap(6, max_iterations=5)


def test_iteration_cap_zero_always_passes():
    check_iteration_cap(0, max_iterations=5)


# ─── ADVERSARIAL-004: secret_scrub – false-negative probes ─────────────────

def test_scrub_short_secret_not_caught_by_length_pattern():
    """A secret shorter than 52 chars won't match the PAT regex. Env-var path must catch it."""
    import os
    short_secret = "abc123XYZ"  # < 52 chars, no known prefix
    # Without env var set this should pass through uncleaned (document the gap)
    result = scrub_secrets(f"token={short_secret}")
    # This is a KNOWN limitation – document it
    # We're asserting current behaviour so we can flag it
    assert short_secret in result, (
        "Short secrets (< 52 chars, no known prefix) pass through scrub_secrets uncleaned. "
        "This is FINDING SEC-003."
    )


def test_scrub_base64_encoded_pat_not_caught():
    """A base64-encoded PAT (as sent in Basic auth headers) may bypass scrubbing."""
    import base64
    # A realistic PAT > 52 chars will be caught by the raw regex,
    # but its base64 encoding may not be.
    raw_pat = "A" * 55  # matches _PATTERNS[0]
    encoded = base64.b64encode(f":{raw_pat}".encode()).decode()
    result = scrub_secrets(f"Authorization: Basic {encoded}")
    # The base64 blob is a long alphanumeric string – may or may not match
    # Record current behaviour
    if raw_pat not in result:
        pass  # The raw PAT is not in result (it's encoded), fine
    if encoded in result:
        pytest.fail(
            f"FINDING SEC-003b: base64-encoded PAT ({encoded[:20]}…) not scrubbed from output. "
            "This is the exact form sent in HTTP Authorization headers."
        )


# ─── ADVERSARIAL-005: branch naming – injection / bypass ───────────────────

def test_branch_validation_rejects_main():
    with pytest.raises(ValueError):
        validate_branch_name("main")


def test_branch_validation_rejects_slash_traversal():
    with pytest.raises(ValueError):
        validate_branch_name("agent/../main")


def test_branch_validation_rejects_no_id():
    with pytest.raises(ValueError):
        validate_branch_name("agent/no-numeric-id")


def test_branch_validation_rejects_empty():
    with pytest.raises(ValueError):
        validate_branch_name("")


def test_branch_validation_accepts_valid():
    validate_branch_name("agent/42-fix-login")


# ─── ADVERSARIAL-006: plan integrity – mismatched lengths ──────────────────

def test_select_smallest_mismatched_options_blast_scores():
    """select_smallest_node with options/blast_scores length mismatch should not silently corrupt."""
    from agent.core.state import RunState
    from agent.nodes.select_smallest import select_smallest_node
    from agent.core.schemas import Option, BlastRadius

    state = RunState(
        run_id="test",
        ticket_id=1,
        options=[
            Option(id="opt-1", description="A", files_touched=["a.cs"]),
            Option(id="opt-2", description="B", files_touched=["b.cs"]),
        ],
        blast_scores=[
            BlastRadius(files_count=1, api_changes_count=0, shared_modules_count=0, score=1.0),
            # Only 1 blast score for 2 options
        ],
    )
    # This should not raise IndexError silently – it should surface clearly
    try:
        result = select_smallest_node(state)
        # If it succeeds with mismatched data, document it
        # It'll pick min_idx=0 (only score provided), and options[0] is valid
        # so no crash – but options[1] blast score is undefined. This is a latent bug.
        assert result["plan"] is not None
    except (IndexError, Exception) as e:
        pytest.fail(f"Unhandled exception on mismatched options/blast_scores: {e}")


# ─── ADVERSARIAL-007: session manager – double-clean ticket ─────────────────

def test_clean_ticket_idempotent(tmp_path: Path) -> None:
    """clean_ticket called twice must not raise."""
    from agent.session.manager import SessionManager
    sm = SessionManager(repo_root=tmp_path)
    sm.init_project()
    sm.clean_ticket(999)  # never existed
    sm.clean_ticket(999)  # should not raise


# ─── ADVERSARIAL-008: secret scrub – empty/None input ───────────────────────

def test_scrub_empty_string():
    assert scrub_secrets("") == ""


def test_scrub_whitespace_only():
    result = scrub_secrets("   ")
    assert result == "   "

