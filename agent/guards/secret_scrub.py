"""Secret scrubbing guardrail.

Ensures no credentials, PATs, API keys, or connection strings enter prompts,
state, traces, or logs.
"""

import os
import re

# Common secret pattern matchers
_PATTERNS: list[re.Pattern[str]] = [
    # Azure DevOps PAT format (52-88 alphanumeric characters)
    re.compile(r"\b[A-Za-z0-9]{52,88}\b"),
    # Bearer authentication tokens
    re.compile(r"(Bearer\s+)[A-Za-z0-9_\-\.]{20,}", re.IGNORECASE),
    # Common connection string secrets (Password=..., AccountKey=..., etc.)
    re.compile(
        r"((?:password|pwd|accountkey|sharedaccesskey|secret|token)\s*=\s*)([^;\s]+)",
        re.IGNORECASE,
    ),
    # PEM private keys
    re.compile(
        r"-----BEGIN [A-Z\s]+PRIVATE KEY-----[\s\S]*?-----END [A-Z\s]+PRIVATE KEY-----",
        re.MULTILINE,
    ),
    # Generic API keys with common prefixes
    re.compile(r"\b(?:sk|pk|pat)_[A-Za-z0-9_\-]{20,}\b"),
]

_REPLACEMENT = "[REDACTED_SECRET]"


def scrub_secrets(text: str) -> str:
    """Scrub sensitive credentials from text using static patterns and active env secrets."""
    if not text:
        return text

    scrubbed = text

    # 1. Scrub exact values of active environment secrets if present
    for env_var in ("AZURE_DEVOPS_PAT", "OPENCODE_API_KEY", "ADO_PAT", "API_KEY"):
        val = os.getenv(env_var, "").strip()
        if val and len(val) >= 8 and val in scrubbed:
            scrubbed = scrubbed.replace(val, _REPLACEMENT)

    # 2. Scrub regex patterns
    for pattern in _PATTERNS:
        # If pattern captures groups, replace the secret group while preserving prefix
        if pattern.groups == 1:
            scrubbed = pattern.sub(rf"\g<1>{_REPLACEMENT}", scrubbed)
        elif pattern.groups == 2:
            scrubbed = pattern.sub(rf"\g<1>{_REPLACEMENT}", scrubbed)
        else:
            scrubbed = pattern.sub(_REPLACEMENT, scrubbed)

    return scrubbed
