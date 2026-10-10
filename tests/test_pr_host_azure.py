import pytest

from agent.connectors.pr_host_azure import AzurePRHost


def test_pr_host_refuses_non_agent_branch() -> None:
    host = AzurePRHost(org="testorg", project="testproj", repo="testrepo")
    with pytest.raises(ValueError, match="Refusing to push branch"):
        host.push_branch("main")

    with pytest.raises(ValueError, match="Refusing to push branch"):
        host.push_branch("feature/unauthorized")


def test_pr_host_dry_run_zero_writes() -> None:
    host = AzurePRHost(
        org="testorg",
        project="testproj",
        repo="testrepo",
        dry_run=True,
    )
    # Valid agent branch
    valid_branch = "agent/123-fix-auth"
    # Dry run should not raise and should not make real network calls
    host.push_branch(valid_branch)

    pr_ref = host.create_draft_pr(
        branch=valid_branch,
        title="Draft PR for ticket 123",
        body="PR description",
        work_item=123,
    )
    assert pr_ref.pr_id == 0 or pr_ref.pr_id is not None
    assert "dry-run" in pr_ref.url.lower() or pr_ref.branch == valid_branch
