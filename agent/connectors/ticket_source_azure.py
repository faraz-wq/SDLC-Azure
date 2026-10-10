"""Azure DevOps TicketSource implementation.

Communicates with Azure DevOps Work Item Tracking REST APIs.
Secrets come from the environment and outbound text is scrubbed.
"""

import base64
import json
import logging
import os
import urllib.request
from typing import Any

from agent.core.protocols import TicketSource
from agent.core.schemas import Comment, Ticket
from agent.guards.secret_scrub import scrub_secrets

logger = logging.getLogger(__name__)


class AzureTicketSource(TicketSource):
    """Azure DevOps work item connector."""

    def __init__(
        self,
        org: str | None = None,
        project: str | None = None,
        pat: str | None = None,
        dry_run: bool = False,
    ) -> None:
        self.org = org or os.getenv("AZURE_DEVOPS_ORG", "")
        self.project = project or os.getenv("AZURE_DEVOPS_PROJECT", "")
        self._pat = pat or os.getenv("AZURE_DEVOPS_PAT", "")
        self.dry_run = dry_run
        self.base_url = f"https://dev.azure.com/{self.org}/{self.project}"

    def _headers(self) -> dict[str, str]:
        auth = base64.b64encode(f":{self._pat}".encode()).decode()
        return {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
        }

    def parse_raw_work_item(
        self, raw_wi: dict[str, Any], raw_comments: list[dict[str, Any]]
    ) -> Ticket:
        """Parse raw Azure DevOps work item JSON into normalized Ticket model."""
        fields: dict[str, Any] = raw_wi.get("fields", {})
        title: str = str(fields.get("System.Title", ""))
        desc: str = str(fields.get("System.Description", ""))

        # Acceptance criteria
        ac_raw: str = str(fields.get("Microsoft.VSTS.Common.AcceptanceCriteria", ""))
        ac_clean = (
            ac_raw.replace("<br/>", "\n").replace("<p>", "").replace("</p>", "\n").split("\n")
        )
        criteria: list[str] = [c.strip() for c in ac_clean if c.strip()]

        # Tags
        tags_raw: str = str(fields.get("System.Tags", ""))
        tags: list[str] = [t.strip() for t in tags_raw.split(";") if t.strip()]

        # Linked items
        linked_items: list[int] = []
        relations: list[dict[str, Any]] = raw_wi.get("relations", [])
        for rel in relations:
            url: str = str(rel.get("url", ""))
            if "/workItems/" in url or url.rstrip("/").split("/")[-1].isdigit():
                try:
                    linked_items.append(int(url.rstrip("/").split("/")[-1]))
                except ValueError:
                    pass

        # Comments
        comments: list[Comment] = []
        for c in raw_comments:
            c_text: str = str(c.get("text", ""))
            author_info: dict[str, Any] = c.get("createdBy", {})
            author: str = str(author_info.get("displayName", "Unknown"))
            comments.append(
                Comment(
                    id=str(c.get("id", "")),
                    author=author,
                    body=c_text,
                )
            )

        return Ticket(
            id=int(raw_wi.get("id", 0)),
            title=title,
            description=desc,
            acceptance_criteria=criteria,
            comments=comments,
            linked_items=linked_items,
            tags=tags,
        )

    def get_ticket(self, id: int) -> Ticket:
        """Fetch work item and comments via ADO REST API."""
        url = f"{self.base_url}/_apis/wit/workitems/{id}?$expand=all&api-version=7.1"
        req = urllib.request.Request(url, headers=self._headers())

        with urllib.request.urlopen(req) as resp:
            raw_wi: dict[str, Any] = json.loads(resp.read().decode())

        # Fetch comments
        comments_url = (
            f"{self.base_url}/_apis/wit/workitems/{id}/comments?api-version=7.1-preview.3"
        )
        raw_comments: list[dict[str, Any]] = []
        try:
            req_c = urllib.request.Request(comments_url, headers=self._headers())
            with urllib.request.urlopen(req_c) as resp_c:
                c_data: dict[str, Any] = json.loads(resp_c.read().decode())
                raw_comments = c_data.get("comments", [])
        except Exception as e:
            logger.warning(f"Could not load comments for ticket {id}: {e}")

        return self.parse_raw_work_item(raw_wi, raw_comments)

    def post_comment(self, id: int, body: str) -> None:
        """Post a comment to the work item. No-op in dry-run mode."""
        clean_body = scrub_secrets(body)
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would post comment to ticket {id}: {clean_body[:60]}...")
            return

        url = f"{self.base_url}/_apis/wit/workitems/{id}/comments?api-version=7.1-preview.3"
        payload = json.dumps({"text": clean_body}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=self._headers(), method="POST")

        with urllib.request.urlopen(req) as resp:
            if resp.status not in (200, 201):
                logger.error(f"Failed to post comment to ticket {id}: status {resp.status}")

    def set_tag(self, id: int, tag: str, present: bool) -> None:
        """Add or remove a tag from the work item. No-op in dry-run mode."""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would set tag '{tag}' (present={present}) on ticket {id}")
            return

        ticket = self.get_ticket(id)
        current_tags = set(ticket.tags)
        if present:
            current_tags.add(tag)
        else:
            current_tags.discard(tag)

        new_tags_val = "; ".join(sorted(current_tags))
        patch_payload = [
            {
                "op": "add",
                "path": "/fields/System.Tags",
                "value": new_tags_val,
            }
        ]

        url = f"{self.base_url}/_apis/wit/workitems/{id}?api-version=7.1"
        headers = self._headers()
        headers["Content-Type"] = "application/json-patch+json"
        req = urllib.request.Request(
            url,
            data=json.dumps(patch_payload).encode("utf-8"),
            headers=headers,
            method="PATCH",
        )

        with urllib.request.urlopen(req) as resp:
            if resp.status not in (200, 201):
                logger.error(f"Failed to set tag on ticket {id}: status {resp.status}")

    def new_replies_since(self, id: int, marker: str) -> list[Comment]:
        """Fetch comments added after the specified marker."""
        ticket = self.get_ticket(id)
        replies: list[Comment] = []
        found_marker = False
        for c in ticket.comments:
            if found_marker:
                replies.append(c)
            elif marker in c.body:
                found_marker = True
        return replies
