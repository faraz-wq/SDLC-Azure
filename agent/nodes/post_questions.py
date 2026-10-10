"""Post questions node: queues pending clarification questions on HumanChannel."""

from typing import Any

from agent.core.protocols import HumanChannel
from agent.core.schemas import HumanRequest
from agent.core.state import RunState


def post_questions_node(state: RunState, channel: HumanChannel) -> dict[str, Any]:
    """Queue clarification questions for human interaction and set status to waiting."""
    if not state.clarification_questions:
        return {"status": "running"}

    prompt_lines = [f"{i + 1}. {q}" for i, q in enumerate(state.clarification_questions)]
    prompt_text = "Please clarify the following questions to proceed:\n" + "\n".join(prompt_lines)

    session_id = f"ado-{state.ticket_id}"
    request = HumanRequest(
        session_id=session_id,
        request_type="questions",
        prompt=prompt_text,
        options=state.clarification_questions,
    )

    channel.ask(session_id, request)

    return {
        "status": "waiting_on_human",
        "messages": [
            *state.messages,
            (
                f"Queued {len(state.clarification_questions)} clarification questions "
                f"in session {session_id}."
            ),
        ],
    }
