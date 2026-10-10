from agent.llm.opencode_client import OpenCodeClient


def test_opencode_client_model_role_resolution() -> None:
    client = OpenCodeClient(api_key="test-key")
    model_name = client.resolve_model("clarify")
    assert model_name == "glm-5.3-flash" or "flash" in model_name


def test_opencode_client_denylist_rejection() -> None:
    client = OpenCodeClient(api_key="test-key")
    assert client.is_denylisted("muse-spark-1.2-contributor") is True
    assert client.is_denylisted("glm-5.3-flash") is False
