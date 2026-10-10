"""State machine graph definition.

End-to-end SDLC pipeline:
ingest -> clarify_score -> post_questions (interrupt) -> impact_analysis
-> propose_options -> blast_score -> select_smallest -> approve_plan (interrupt)
-> write_tests -> confirm_red -> implement <-> verify -> approve_pr (interrupt)
-> raise_draft_pr -> done
"""

from pathlib import Path
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agent.core.protocols import HumanChannel, LLMClient, PRHost, TicketSource
from agent.core.state import RunState
from agent.nodes.approve_plan import approve_plan_node
from agent.nodes.approve_pr import approve_pr_node
from agent.nodes.blast_score import blast_score_node
from agent.nodes.clarify_score import clarify_score_node
from agent.nodes.confirm_red import confirm_red_node
from agent.nodes.impact_analysis import impact_analysis_node
from agent.nodes.implement import implement_node
from agent.nodes.ingest import ingest_node
from agent.nodes.post_questions import post_questions_node
from agent.nodes.propose_options import propose_options_node
from agent.nodes.raise_draft_pr import raise_draft_pr_node
from agent.nodes.select_smallest import select_smallest_node
from agent.nodes.verify import verify_node
from agent.nodes.write_tests import write_tests_node


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


def create_full_sdlc_graph(
    ticket_source: TicketSource,
    pr_host: PRHost,
    llm: LLMClient,
    channel: HumanChannel,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
    repo_root: Path | None = None,
) -> CompiledStateGraph[RunState, Any, Any, Any]:
    """Build and compile the complete end-to-end SDLC state machine."""
    builder: StateGraph[RunState] = StateGraph(RunState)

    def _ingest(state: RunState) -> dict[str, Any]:
        return ingest_node(state, ticket_source)

    def _clarify_score(state: RunState) -> dict[str, Any]:
        return clarify_score_node(state, llm)

    def _post_questions(state: RunState) -> dict[str, Any]:
        return post_questions_node(state, channel)

    def _propose_options(state: RunState) -> dict[str, Any]:
        return propose_options_node(state, llm)

    def _approve_plan(state: RunState) -> dict[str, Any]:
        return approve_plan_node(state, channel)

    def _write_tests(state: RunState) -> dict[str, Any]:
        return write_tests_node(state, llm)

    def _implement(state: RunState) -> dict[str, Any]:
        return implement_node(state, repo_root)

    def _approve_pr(state: RunState) -> dict[str, Any]:
        return approve_pr_node(state, channel)

    def _raise_draft_pr(state: RunState) -> dict[str, Any]:
        return raise_draft_pr_node(state, pr_host)

    builder.add_node("ingest", _ingest)
    builder.add_node("clarify_score", _clarify_score)
    builder.add_node("post_questions", _post_questions)
    builder.add_node("impact_analysis", impact_analysis_node)
    builder.add_node("propose_options", _propose_options)
    builder.add_node("blast_score", blast_score_node)
    builder.add_node("select_smallest", select_smallest_node)
    builder.add_node("approve_plan", _approve_plan)
    builder.add_node("write_tests", _write_tests)
    builder.add_node("confirm_red", confirm_red_node)
    builder.add_node("implement", _implement)
    builder.add_node("verify", verify_node)
    builder.add_node("approve_pr", _approve_pr)
    builder.add_node("raise_draft_pr", _raise_draft_pr)

    builder.add_edge(START, "ingest")
    builder.add_edge("ingest", "clarify_score")

    def _route_clarify(s: RunState) -> str:
        if s.stage == "clarify" and s.clarification_questions:
            return "post_questions"
        return "impact_analysis"

    builder.add_conditional_edges(
        "clarify_score",
        _route_clarify,
        {"post_questions": "post_questions", "impact_analysis": "impact_analysis"},
    )
    builder.add_edge("post_questions", "impact_analysis")

    builder.add_edge("impact_analysis", "propose_options")
    builder.add_edge("propose_options", "blast_score")
    builder.add_edge("blast_score", "select_smallest")
    builder.add_edge("select_smallest", "approve_plan")
    builder.add_edge("approve_plan", "write_tests")

    builder.add_edge("write_tests", "confirm_red")
    builder.add_edge("confirm_red", "implement")
    builder.add_edge("implement", "verify")
    builder.add_edge("verify", "approve_pr")
    builder.add_edge("approve_pr", "raise_draft_pr")
    builder.add_edge("raise_draft_pr", END)

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_after=["post_questions", "approve_plan", "approve_pr"],
    )
