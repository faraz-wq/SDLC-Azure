"""Autonomous test harness and evaluation channel implementation.

Follows Section 10 and 14 of ARCHITECTURE.md:
- AutoAnswerChannel resolves clarification questions and human approval gates
- Evaluates against target archetypes and checks rubric scoring, diff limits, and PR creation.
"""

from typing import Any

from agent.core.protocols import HumanChannel
from agent.core.schemas import HumanRequest, HumanResponse


class AutoAnswerChannel(HumanChannel):
    """Automated HumanChannel simulator for headless evaluation benchmarking.

    Answers clarification questions and approves plans/PRs according to benchmark config.
    """

    def __init__(self, auto_approve: bool = True) -> None:
        self.auto_approve = auto_approve
        self.received_requests: list[HumanRequest] = []
        self.clarifications_recorded: list[dict[str, Any]] = []

    def ask(self, session_id: str, request: HumanRequest) -> None:
        self.received_requests.append(request)

    def collect(self, session_id: str) -> HumanResponse | None:
        if not self.received_requests:
            return None

        req = self.received_requests.pop(0)
        if req.request_type == "questions":
            # Auto-answer with concrete domain specifications
            answers = {
                f"q_{i}": "Use standard production configuration and default conventions."
                for i in range(len(req.options) or 3)
            }
            self.clarifications_recorded.append(
                {
                    "session_id": session_id,
                    "prompt": req.prompt,
                    "answers": answers,
                }
            )
            return HumanResponse(
                session_id=session_id,
                decision="answered",
                answers=answers,
            )

        # Plan or PR approval
        return HumanResponse(
            session_id=session_id,
            decision="approved" if self.auto_approve else "rejected",
            feedback="Auto-approved by Eval Harness",
        )
