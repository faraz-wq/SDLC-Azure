import os

import pytest
from dotenv import load_dotenv

from agent.connectors.pr_host_azure import AzurePRHost
from agent.connectors.ticket_source_azure import AzureTicketSource
from agent.llm.opencode_client import OpenCodeClient

load_dotenv()


@pytest.mark.integration
def test_live_ado_connection() -> None:
    org = os.getenv("AZURE_DEVOPS_ORG")
    project = os.getenv("AZURE_DEVOPS_PROJECT")
    pat = os.getenv("AZURE_DEVOPS_PAT")
    if not (org and project and pat):
        pytest.skip("ADO credentials not available in environment.")

    source = AzureTicketSource(org=org, project=project, pat=pat)
    assert source.org == org
    assert source.project == project

    # Dry-run PR host test against live repo config
    pr_host = AzurePRHost(org=org, project=project, repo="azsdlc", pat=pat, dry_run=True)
    valid_branch = "agent/999-integration-test"
    pr_ref = pr_host.create_draft_pr(
        branch=valid_branch,
        title="Integration test draft PR",
        body="Testing ADO PR creation logic in dry-run mode",
        work_item=999,
    )
    assert pr_ref.branch == valid_branch
    assert pr_ref.pr_id == 0


@pytest.mark.integration
def test_live_opencode_completion() -> None:
    api_key = os.getenv("OPENCODE_API_KEY")
    if not api_key:
        pytest.skip("OpenCode API key not available in environment.")

    client = OpenCodeClient(api_key=api_key, timeout=15)
    res = client.complete(
        role="clarify",
        messages=[{"role": "user", "content": "Respond with the single word 'OK'."}],
        max_output_tokens=50,
        session_id="test-integration",
    )
    assert res.text != ""
    assert res.usage.get("total_tokens", 0) > 0
