"""State machine graph definition."""

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agent.core.protocols import HumanChannel, LLMClient, TicketSource
from agent.core.state import RunState
from agent.nodes.clarify_score import clarify_score_node
from agent.nodes.ingest import ingest_node
from agent.nodes.post_questions import post_questions_node


def node_a(state: RunState) -> dict[str, Any]:
    """First skeleton processing node."""
    return {
        "step_count": state.step_count + 1,
        "messages": [*state.messages, "Processed by node_a"],
        "status": "running",
    }


def node_b(state: RunState) -> dict[str, Any]:
    """Second skeleton processing node."""
    return {
        "step_count": state.step_count + 1,
        "messages": [*state.messages, "Processed by node_b"],
        "status": "completed",
    }


def create_skeleton_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph[RunState, Any, Any, Any]:
    """Build and compile the two-node skeleton graph."""
    builder: StateGraph[RunState] = StateGraph(RunState)
    builder.add_node("node_a", node_a)
    builder.add_node("node_b", node_b)
    builder.add_edge(START, "node_a")
    builder.add_edge("node_a", "node_b")
    builder.add_edge("node_b", END)

    if checkpointer is not None:
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()


def create_clarify_graph(
    ticket_source: TicketSource,
    llm: LLMClient,
    channel: HumanChannel,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph[RunState, Any, Any, Any]:
    """Build graph with ingest, rubric scoring, and question posting interrupt."""
    builder: StateGraph[RunState] = StateGraph(RunState)

    def _ingest(state: RunState) -> dict[str, Any]:
        return ingest_node(state, ticket_source)

    def _clarify_score(state: RunState) -> dict[str, Any]:
        return clarify_score_node(state, llm)

    def _post_questions(state: RunState) -> dict[str, Any]:
        return post_questions_node(state, channel)

    builder.add_node("ingest", _ingest)
    builder.add_node("clarify_score", _clarify_score)
    builder.add_node("post_questions", _post_questions)

    builder.add_edge(START, "ingest")
    builder.add_edge("ingest", "clarify_score")

    def _route_after_clarify(state: RunState) -> str:
        if state.stage == "clarify" and state.clarification_questions:
            return "post_questions"
        return END

    builder.add_conditional_edges(
        "clarify_score",
        _route_after_clarify,
        {"post_questions": "post_questions", END: END},
    )
    builder.add_edge("post_questions", END)

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_after=["post_questions"],
    )
