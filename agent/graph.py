"""State machine graph definition."""

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agent.core.state import RunState


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
