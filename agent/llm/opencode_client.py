"""OpenCode Go inference client implementation."""

import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from agent.core.protocols import LLMClient, LLMResult

logger = logging.getLogger(__name__)


class OpenCodeClient(LLMClient):
    """Inference client talking to OpenCode Go API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://opencode.ai/zen/go/v1",
        config_path: Path | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENCODE_API_KEY", "")
        self.base_url = base_url.rstrip("/")

        # Load models.yaml
        cfg_file = config_path or (Path(__file__).parent / "models.yaml")
        self.roles: dict[str, str] = {}
        self.denylist: list[str] = []
        if cfg_file.exists():
            data: dict[str, Any] = yaml.safe_load(cfg_file.read_text()) or {}
            self.roles = data.get("roles", {})
            self.denylist = data.get("denylist", [])

    def is_denylisted(self, model_id: str) -> bool:
        """Check if model is on the safety denylist."""
        return model_id in self.denylist

    def resolve_model(self, role: str) -> str:
        """Resolve role to concrete model identifier."""
        model = self.roles.get(role, "glm-5.3-flash")
        if self.is_denylisted(model):
            raise ValueError(f"Model '{model}' assigned to role '{role}' is denylisted.")
        return model

    def complete(
        self,
        role: str,
        messages: list[dict[str, str]],
        *,
        schema: type[BaseModel] | None = None,
        max_output_tokens: int = 4096,
        session_id: str = "",
    ) -> LLMResult:
        """Execute chat completion against OpenCode Go."""
        model = self.resolve_model(role)
        effective_session = session_id or "ado-session-default"

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_output_tokens,
        }

        # If schema is requested, supply response_format if compatible
        if schema is not None:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ado-sdlc-agent/0.1.0",
            "x-opencode-session": effective_session,
        }

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req) as resp:
            data: dict[str, Any] = json.loads(resp.read().decode())

        choices: list[dict[str, Any]] = data.get("choices", [])
        if not choices:
            raise RuntimeError("OpenCode Go returned 0 choices.")

        choice = choices[0]
        message_data: dict[str, Any] = choice.get("message", {})
        content: str = str(message_data.get("content") or "")
        finish_reason: str = str(choice.get("finish_reason") or "stop")

        usage_raw: dict[str, Any] = data.get("usage", {})
        usage: dict[str, int] = {
            "prompt_tokens": int(usage_raw.get("prompt_tokens", 0)),
            "completion_tokens": int(usage_raw.get("completion_tokens", 0)),
            "total_tokens": int(usage_raw.get("total_tokens", 0)),
        }

        parsed_model: Any | None = None
        if schema is not None and content:
            parsed_model = schema.model_validate_json(content)

        return LLMResult(
            text=content,
            parsed=parsed_model,
            finish_reason=finish_reason,
            usage=usage,
            model_id=model,
        )
