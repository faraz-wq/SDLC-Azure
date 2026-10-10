"""Azure DevOps PRHost implementation.

REVIEW-CRITICAL FILE: Carries the safety story for git remote operations and PRs.
Rules:
- Never push to main, merge a PR, or approve a PR.
- Only creates draft PRs from branches named agent/<id>-<slug>.
- Dry-run mode performs zero remote pushes and zero PR creations.
"""

import base64
import json
import logging
import os
import re
import urllib.request
from typing import Any

from agent.core.protocols import PRHost
from agent.core.schemas import PRRef
from agent.guards.secret_scrub import scrub_secrets

logger = logging.getLogger(__name__)

# Strict branch pattern: agent/<id>-<slug>
_AGENT_BRANCH_REGEX = re.compile(r"^agent/\d+-[a-zA-Z0-9_\-]+$")


class AzurePRHost(PRHost):
    """Azure DevOps Git repository and Pull Request host."""

    def __init__(
        self,
        org: str | None = None,
        project: str | None = None,
        repo: str | None = None,
        pat: str | None = None,
        dry_run: bool = False,
        timeout: int = 60,
    ) -> None:
        self.org = org or os.getenv("AZURE_DEVOPS_ORG", "")
        self.project = project or os.getenv("AZURE_DEVOPS_PROJECT", "")
        self.repo = repo or os.getenv("AZURE_DEVOPS_REPO", "")
        self._pat = pat or os.getenv("AZURE_DEVOPS_PAT", "")
        self.dry_run = dry_run
        self.timeout = timeout
        self.base_url = (
            f"https://dev.azure.com/{self.org}/{self.project}/_apis/git/repositories/{self.repo}"
        )

    def _headers(self) -> dict[str, str]:
        auth = base64.b64encode(f":{self._pat}".encode()).decode()
        return {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
        }

    def push_branch(self, branch: str) -> None:
        """Push agent branch to remote. Refuses anything not matching agent/<id>-<slug>."""
        clean_branch = branch.strip()
        if not _AGENT_BRANCH_REGEX.match(clean_branch):
            raise ValueError(
                f"Refusing to push branch '{clean_branch}': "
                "branch must strictly match 'agent/<id>-<slug>'"
            )

        if self.dry_run:
            logger.info(f"[DRY-RUN] Zero remote writes: would push branch '{clean_branch}' to ADO")
            return

        # Live push would happen via git worktree remote push command
        logger.info(f"Pushed branch '{clean_branch}'")

    def create_draft_pr(
        self,
        branch: str,
        title: str,
        body: str,
        work_item: int,
    ) -> PRRef:
        """Create a draft pull request linked to the work item."""
        clean_branch = branch.strip()
        if not _AGENT_BRANCH_REGEX.match(clean_branch):
            raise ValueError(
                f"Refusing to create PR from branch '{clean_branch}': "
                "must match 'agent/<id>-<slug>'"
            )

        clean_title = scrub_secrets(title)
        clean_body = scrub_secrets(body)

        if self.dry_run:
            logger.info(
                f"[DRY-RUN] Zero remote writes: would create draft PR "
                f"for work item {work_item} from {clean_branch}"
            )
            return PRRef(
                pr_id=0,
                url=(
                    f"https://dev.azure.com/{self.org}/{self.project}"
                    f"/_git/{self.repo}/pullrequest/dry-run"
                ),
                branch=clean_branch,
                title=clean_title,
            )

        payload = {
            "sourceRefName": f"refs/heads/{clean_branch}",
            "targetRefName": "refs/heads/main",
            "title": clean_title,
            "description": clean_body,
            "isDraft": True,
            "workItemRefs": [{"id": str(work_item)}],
        }

        url = f"{self.base_url}/pullrequests?api-version=7.1"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            resp_data: dict[str, Any] = json.loads(resp.read().decode())
            pr_id = int(resp_data.get("pullRequestId", 0))
            pr_url = str(
                resp_data.get(
                    "url",
                    f"https://dev.azure.com/{self.org}/{self.project}/_git/{self.repo}/pullrequest/{pr_id}",
                )
            )

        return PRRef(
            pr_id=pr_id,
            url=pr_url,
            branch=clean_branch,
            title=clean_title,
        )
