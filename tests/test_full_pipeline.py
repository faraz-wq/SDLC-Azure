import sqlite3
from pathlib import Path

import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver

from agent.core.protocols import (
    CodingAgent,
    HumanChannel,
    LLMClient,
    LLMResult,
    PRHost,
    TicketSource,
)
from agent.core.schemas import (
    BlastRadius,
    CodingResult,
    CodingTask,
    Comment,
    HumanRequest,
    HumanResponse,
    Limits,
    Option,
    Plan,
    PRRef,
    Ticket,
)
from agent.core.state import RunState
from agent.graph import create_full_sdlc_graph
from agent.guards.diff_cap import DiffCapViolationError, check_diff_cap
from agent.guards.iteration_cap import IterationCapViolationError, check_iteration_cap
from agent.guards.scope_guard import ScopeViolationError, check_scope


class MockTicketSource(TicketSource):
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


class MockPRHost(PRHost):
    def __init__(self) -> None:
        self.created_prs: list[dict[str, str | int]] = []

    def create_draft_pr(self, branch: str, title: str, body: str, work_item: int) -> PRRef:
        self.created_prs.append({"branch": branch, "title": title, "work_item": work_item})
        return PRRef(
            pr_id=101,
            url="https://dev.azure.com/testorg/testproj/_git/repo/pullrequest/101",
            branch=branch,
            title=title,
        )

    def push_branch(self, branch: str) -> None:
        pass


class FakeCodingAgent(CodingAgent):
    def run(self, task: CodingTask, wt: Path, limits: Limits) -> CodingResult:
        return CodingResult(iterations=1, tokens=50, final_diff="", success=True)


class MockLLMClient(LLMClient):
    def complete(
        self,
        role: str,
        messages: list[dict[str, str]],
        *,
        schema: type | None = None,
        max_output_tokens: int = 4096,
        session_id: str = "",
    ) -> LLMResult:
        if role == "clarify":
            return LLMResult(
                text='{"score": 9.5, "questions": []}',
                finish_reason="stop",
                usage={"total_tokens": 15},
                model_id="mock-glm",
            )
        elif role == "plan":
            return LLMResult(
                text="""{
                    "options": [
                        {
                            "id": "opt-1",
                            "description": "Minimal targeted fix",
                            "files_touched": ["src/Controllers/AuthController.cs"],
                            "expected_api_changes": []
                        }
                    ]
                }""",
                finish_reason="stop",
                usage={"total_tokens": 30},
                model_id="mock-deepseek",
            )
        return LLMResult(
            text="Mock response",
            finish_reason="stop",
            usage={"total_tokens": 10},
            model_id="mock-model",
        )


class MockHumanChannel(HumanChannel):
    def __init__(self) -> None:
        self.requests: list[HumanRequest] = []

    def ask(self, session_id: str, request: HumanRequest) -> None:
        self.requests.append(request)

    def collect(self, session_id: str) -> HumanResponse | None:
        return None


def test_guardrails_enforcement() -> None:
    # Test diff cap
    check_diff_cap(100, max_cap=300)
    with pytest.raises(DiffCapViolationError):
        check_diff_cap(350, max_cap=300)

    # Test iteration cap
    check_iteration_cap(3, max_iterations=5)
    with pytest.raises(IterationCapViolationError):
        check_iteration_cap(6, max_iterations=5)

    # Test scope guard
    plan = Plan(
        ticket_id=12,
        summary="Test plan",
        chosen_option=Option(
            id="opt-1",
            description="Fix auth",
            files_touched=["src/Auth/*"],
            expected_api_changes=[],
        ),
        rejected_options=[],
        blast=BlastRadius(files_count=1, api_changes_count=0, shared_modules_count=0, score=1.0),
        allowed_files=["src/Auth/*"],
        max_diff_lines=100,
        expected_api_changes=[],
        test_targets=[],
    )

    # Inside scope
    check_scope(["src/Auth/Token.cs"], diff_lines=50, plan=plan)

    # Outside allowed files
    with pytest.raises(ScopeViolationError):
        check_scope(["src/Billing/Payment.cs"], diff_lines=50, plan=plan)

    # Exceeding diff lines
    with pytest.raises(ScopeViolationError):
        check_scope(["src/Auth/Token.cs"], diff_lines=150, plan=plan)


def test_full_pipeline_execution_with_human_interrupts(tmp_path: Path) -> None:
    ticket = Ticket(
        id=777,
        title="Fix user authentication timeout",
        description="Users report getting logged out prematurely",
        acceptance_criteria=["Session persists for 24 hours"],
        comments=[],
    )
    source = MockTicketSource(ticket)
    pr_host = MockPRHost()
    llm = MockLLMClient()
    channel = MockHumanChannel()

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    checkpointer.setup()

    graph = create_full_sdlc_graph(
        ticket_source=source,
        pr_host=pr_host,
        llm=llm,
        channel=channel,
        checkpointer=checkpointer,
        repo_root=tmp_path,
        coding_agent=FakeCodingAgent(),
    )

    config: RunnableConfig = {"configurable": {"thread_id": "ado-777"}}

    # Phase 1: Start run -> Ingest -> Clarify -> Plan -> Pauses at approve_plan
    initial_state = RunState(run_id="run-777", ticket_id=777)
    res_phase1 = graph.invoke(initial_state, config=config)

    assert res_phase1["status"] == "waiting_on_human"
    assert res_phase1["stage"] == "plan_approval"
    assert res_phase1["plan"] is not None
    assert len(channel.requests) == 1
    assert channel.requests[0].request_type == "plan_approval"

    # Phase 2: Human Approves Plan -> Resume -> Write Tests -> Confirm Red ->
    # Implement -> Verify -> Pauses at approve_pr
    graph.update_state(config, {"status": "running"}, as_node="approve_plan")
    res_phase2 = graph.invoke(None, config=config)

    assert res_phase2["status"] == "waiting_on_human"
    assert res_phase2["stage"] == "pr_approval"
    assert len(channel.requests) == 2
    assert channel.requests[1].request_type == "pr_approval"

    # Phase 3: Human Approves PR -> Resume -> Raise Draft PR -> Completed
    graph.update_state(config, {"status": "running"}, as_node="approve_pr")
    res_phase3 = graph.invoke(None, config=config)

    assert res_phase3["status"] == "done"
    assert res_phase3["stage"] == "complete"
    assert res_phase3["pr_ref"] is not None
    assert res_phase3["pr_ref"].pr_id == 101
    assert len(pr_host.created_prs) == 1
    assert pr_host.created_prs[0]["work_item"] == 777

    conn.close()
