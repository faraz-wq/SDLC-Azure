import sqlite3
from pathlib import Path

import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
from pydantic import ValidationError

from agent.core.state import RunState
from agent.graph import create_skeleton_graph


def test_skeleton_graph_execution() -> None:
    """Test standard execution of the two-node skeleton graph."""
    graph = create_skeleton_graph()
    initial_state = RunState(run_id="test-run-1")

    result = graph.invoke(initial_state)

    assert result["run_id"] == "test-run-1"
    assert result["step_count"] == 2
    assert result["status"] == "completed"
    assert "Processed by node_a" in result["messages"]
    assert "Processed by node_b" in result["messages"]


def test_skeleton_graph_checkpointing(tmp_path: Path) -> None:
    """Test checkpointing state with SQLite checkpointer."""
    db_path = str(tmp_path / "checkpoints.sqlite")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    checkpointer.setup()

    graph = create_skeleton_graph(checkpointer=checkpointer)
    config: RunnableConfig = {"configurable": {"thread_id": "thread-123"}}

    initial_state = RunState(run_id="test-run-thread")
    result = graph.invoke(initial_state, config=config)

    assert result["step_count"] == 2
    assert result["status"] == "completed"

    # Verify checkpointer saved state
    saved_state = graph.get_state(config)
    assert saved_state is not None
    assert saved_state.values["run_id"] == "test-run-thread"
    assert saved_state.values["status"] == "completed"
    assert saved_state.values["step_count"] == 2
    conn.close()


def test_skeleton_graph_validation_failure() -> None:
    """Failure path test: RunState requires run_id, invalid instantiation raises ValidationError."""
    with pytest.raises(ValidationError):
        # Missing required run_id
        RunState.model_validate({"messages": ["invalid"]})
