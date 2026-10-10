"""Agent configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Automatically load .env if present
load_dotenv()


class AgentConfig(BaseModel):
    """Runtime configuration for the SDLC agent."""

    # Operational modes
    dry_run: bool = Field(default=False)

    # Azure DevOps Settings
    azure_devops_org: str = Field(default_factory=lambda: os.getenv("AZURE_DEVOPS_ORG", ""))
    azure_devops_project: str = Field(default_factory=lambda: os.getenv("AZURE_DEVOPS_PROJECT", ""))
    azure_devops_repo: str = Field(default_factory=lambda: os.getenv("AZURE_DEVOPS_REPO", ""))

    # Limits and Caps
    max_iterations: int = Field(default=5)
    max_diff_lines: int = Field(default=300)
    external_timeout_seconds: int = Field(default=60)

    # Paths
    project_root: Path = Field(default_factory=Path.cwd)
    dot_agent_dir: Path = Field(default_factory=lambda: Path.cwd() / ".agent")

    @property
    def checkpointer_db_path(self) -> Path:
        """Path to SQLite checkpoints database."""
        return self.dot_agent_dir / "sessions.sqlite"
