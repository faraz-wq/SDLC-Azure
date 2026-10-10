from agent.connectors.ticket_source_azure import AzureTicketSource


def test_ticket_source_parse_ado_payload() -> None:
    source = AzureTicketSource(org="testorg", project="testproj")
    raw_wi = {
        "id": 42,
        "fields": {
            "System.Title": "Sample Ticket",
            "System.Description": "Detailed problem description",
            "Microsoft.VSTS.Common.AcceptanceCriteria": "Criteria 1<br/>Criteria 2",
            "System.Tags": "backend; auth",
        },
        "relations": [{"rel": "System.LinkTypes.Hierarchy-Forward", "url": "https://.../43"}],
    }

    ticket = source.parse_raw_work_item(raw_wi, raw_comments=[])
    assert ticket.id == 42
    assert ticket.title == "Sample Ticket"
    assert "Criteria 1" in ticket.acceptance_criteria[0]
    assert "backend" in ticket.tags
    assert 43 in ticket.linked_items


def test_ticket_source_dry_run_zero_writes() -> None:
    source = AzureTicketSource(org="testorg", project="testproj", dry_run=True)
    # Both should be no-ops without error in dry-run mode
    source.post_comment(42, "Dry run comment")
    source.set_tag(42, "needs-clarification", True)
