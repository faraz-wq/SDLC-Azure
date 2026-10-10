from typing import Any

from pydantic import BaseModel

from agent.core.protocols import HumanChannel, LLMClient, LLMResult, TicketSource
from agent.core.schemas import Comment, HumanRequest, HumanResponse, Ticket
from agent.core.state import RunState
from agent.nodes.clarify_score import clarify_score_node
from agent.nodes.ingest import ingest_node
from agent.nodes.post_questions import post_questions_node


class DummyTicketSource(TicketSource):
    def __init__(self, ticket: Ticket) -> None:
        self.ticket = ticket

    def get_ticket(self, id: int) -> Ticket:
        return self.ticket

    def post_comment(self, id: int, body: str) -> None:
        pass

    def set_tag(self, id: int, tag: str, present: bool) -> None:
        pass

    def new_replies_since(self, id: int, marker: str) -> list[Comment]:
        return []


class DummyLLMClient(LLMClient):
    def __init__(self, response_text: str = "", parsed: Any | None = None) -> None:
        self.response_text = response_text
        self.parsed = parsed

    def complete(
        self,
        role: str,
        messages: list[dict[str, str]],
        *,
        schema: type[BaseModel] | None = None,
        max_output_tokens: int = 4096,
        session_id: str = "",
    ) -> LLMResult:
        return LLMResult(
            text=self.response_text,
            parsed=self.parsed,
            finish_reason="stop",
            usage={"total_tokens": 10},
            model_id="fake-llm",
        )


class DummyHumanChannel(HumanChannel):
    def __init__(self) -> None:
        self.requests: list[HumanRequest] = []

    def ask(self, session_id: str, request: HumanRequest) -> None:
        self.requests.append(request)

    def collect(self, session_id: str) -> HumanResponse | None:
        return None


def test_ingest_node() -> None:
    ticket = Ticket(
        id=55,
        title="Add user roles",
        description="Users must have admin or reader roles",
        acceptance_criteria=["Role assigned on login"],
    )
    source = DummyTicketSource(ticket)
    state = RunState(run_id="run-55", ticket_id=55)

    update = ingest_node(state, source)
    assert update["ticket"] is not None
    assert update["ticket"].id == 55
    assert update["stage"] == "clarify"


def test_clarify_score_absorbs_comment_answers() -> None:
    ticket = Ticket(
        id=55,
        title="Add user roles",
        description="Needs roles",
        comments=[
            Comment(id="c1", author="PM", body="Answer: The default role should be 'reader'.")
        ],
    )
    llm = DummyLLMClient(response_text='{"score": 9.0, "questions": []}')
    state = RunState(run_id="run-55", ticket_id=55, ticket=ticket)

    update = clarify_score_node(state, llm)
    # Answers in comments should be absorbed
    assert len(update["clarification_answers"]) > 0
    assert "reader" in str(update["clarification_answers"])
    assert update["stage"] == "impact"


def test_post_questions_queues_and_pauses() -> None:
    channel = DummyHumanChannel()
    state = RunState(
        run_id="run-55",
        ticket_id=55,
        clarification_questions=["What is the max session length?"],
        status="running",
    )

    update = post_questions_node(state, channel)
    assert update["status"] == "waiting_on_human"
    assert len(channel.requests) == 1
    assert channel.requests[0].session_id == "ado-55"
    assert "max session length" in channel.requests[0].prompt


def test_clarify_graph_interrupt_and_resume() -> None:
    import sqlite3

    from langchain_core.runnables import RunnableConfig
    from langgraph.checkpoint.sqlite import SqliteSaver

    from agent.graph import create_clarify_graph

    ticket = Ticket(
        id=66,
        title="Payment gateway error",
        description="Vague bug report",
        acceptance_criteria=[],
    )
    source = DummyTicketSource(ticket)
    llm = DummyLLMClient(
        response_text='{"score": 4.0, "questions": ["Which payment provider failed?"]}'
    )
    channel = DummyHumanChannel()

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    checkpointer.setup()

    graph = create_clarify_graph(source, llm, channel, checkpointer=checkpointer)
    config: RunnableConfig = {"configurable": {"thread_id": "ado-66"}}

    initial = RunState(run_id="run-66", ticket_id=66)
    result = graph.invoke(initial, config=config)

    # Paused at interrupt_after post_questions
    assert result["status"] == "waiting_on_human"
    assert len(channel.requests) == 1
    assert "Which payment provider failed?" in channel.requests[0].prompt

    # State in checkpointer reflects waiting status
    saved = graph.get_state(config)
    assert saved is not None
    assert saved.values["status"] == "waiting_on_human"
    conn.close()
