"""Ingest node: pulls ticket via TicketSource and scrubs secrets."""

from typing import Any

from agent.core.protocols import TicketSource
from agent.core.schemas import Comment, Ticket
from agent.core.state import RunState
from agent.guards.secret_scrub import scrub_secrets


def ingest_node(state: RunState, ticket_source: TicketSource) -> dict[str, Any]:
    """Ingest work item, scrub sensitive text, and prepare for rubric scoring."""
    raw_ticket = ticket_source.get_ticket(state.ticket_id)

    # Scrub all text before storing in graph state
    clean_desc = scrub_secrets(raw_ticket.description)
    clean_criteria = [scrub_secrets(c) for c in raw_ticket.acceptance_criteria]
    clean_comments = [
        Comment(
            id=c.id,
            author=c.author,
            body=scrub_secrets(c.body),
            created_at=c.created_at,
        )
        for c in raw_ticket.comments
    ]

    clean_ticket = Ticket(
        id=raw_ticket.id,
        title=scrub_secrets(raw_ticket.title),
        description=clean_desc,
        acceptance_criteria=clean_criteria,
        comments=clean_comments,
        linked_items=raw_ticket.linked_items,
        tags=raw_ticket.tags,
    )

    return {
        "ticket": clean_ticket,
        "stage": "clarify",
        "messages": [*state.messages, f"Ingested ticket #{clean_ticket.id}: {clean_ticket.title}"],
    }
