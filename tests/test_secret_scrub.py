from agent.guards.secret_scrub import scrub_secrets


def test_scrub_azure_devops_pat() -> None:
    fake_pat = "SampleFakeAzureDevOpsPatStringForUnitTestingScrubberGuards1234567890abcdef"
    text = f"Using PAT authorization: {fake_pat} for API call"
    scrubbed = scrub_secrets(text)
    assert fake_pat not in scrubbed
    assert "[REDACTED_SECRET]" in scrubbed


def test_scrub_bearer_token() -> None:
    text = "Authorization: Bearer secret_opencode_token_1234567890abcdef"
    scrubbed = scrub_secrets(text)
    assert "secret_opencode_token_1234567890abcdef" not in scrubbed
    assert "Bearer [REDACTED_SECRET]" in scrubbed or "[REDACTED_SECRET]" in scrubbed


def test_scrub_clean_text_unchanged() -> None:
    clean_text = "This is a regular ticket description with no credentials."
    assert scrub_secrets(clean_text) == clean_text


def test_scrub_connection_string() -> None:
    text = "Server=tcp:myserver.database.windows.net;Password=SuperSecret123;User=admin;"
    scrubbed = scrub_secrets(text)
    assert "SuperSecret123" not in scrubbed
