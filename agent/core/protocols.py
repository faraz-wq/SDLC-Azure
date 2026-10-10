"""Core protocol interfaces.

Decouples core orchestration from concrete stacks, hosts, tools, and inference providers.
"""

from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, Field

from agent.core.schemas import (
    AppHandle,
    CodingResult,
    CodingTask,
    Comment,
    FailureKind,
    HumanRequest,
    HumanResponse,
    Limits,
    Plan,
    PRRef,
    StepResult,
    TestReport,
    Ticket,
    VerifierReport,
)


class CodeIndex(Protocol):
    """Semantic and syntactic symbol index."""

    def callers(self, symbol: str) -> list[str]: ...
    def usages(self, symbol: str) -> list[str]: ...
    def covering_tests(self, file_path: str) -> list[str]: ...


class TicketSource(Protocol):
    """Work item tracking source (Azure DevOps)."""

    def get_ticket(self, id: int) -> Ticket: ...
    def post_comment(self, id: int, body: str) -> None: ...
    def set_tag(self, id: int, tag: str, present: bool) -> None: ...
    def new_replies_since(self, id: int, marker: str) -> list[Comment]: ...


class PRHost(Protocol):
    """Git repository host and pull request management."""

    def create_draft_pr(self, branch: str, title: str, body: str, work_item: int) -> PRRef: ...
    def push_branch(self, branch: str) -> None: ...


class StackAdapter(Protocol):
    """Language and framework stack adapter."""

    name: str

    def detect(self, repo: Path) -> bool: ...
    def index(self, repo: Path) -> CodeIndex: ...
    def build(self, wt: Path) -> StepResult: ...
    def lint(self, wt: Path) -> StepResult: ...
    def run_tests(self, wt: Path, targets: list[str]) -> TestReport: ...
    def classify_failure(self, report: TestReport) -> FailureKind: ...


class Verifier(Protocol):
    """End-to-end acceptance verifier (Playwright)."""

    def prepare(self, wt: Path) -> AppHandle: ...
    def generate_spec(self, criteria: list[str], plan: Plan) -> list[Path]: ...
    def run(self, app: AppHandle, specs: list[Path]) -> VerifierReport: ...


class CodingAgent(Protocol):
    """Inner-loop coding agent (Pi CLI or test fake)."""

    def run(self, task: CodingTask, wt: Path, limits: Limits) -> CodingResult: ...


class LLMResult(BaseModel):
    """Normalized response from an LLM inference call."""

    text: str
    parsed: Any | None = None
    finish_reason: str = "stop"
    usage: dict[str, int] = Field(default_factory=dict)
    model_id: str = ""


class LLMClient(Protocol):
    """Inference client interface."""

    def complete(
        self,
        role: str,
        messages: list[dict[str, str]],
        *,
        schema: type[BaseModel] | None = None,
        max_output_tokens: int = 4096,
        session_id: str = "",
    ) -> LLMResult: ...


class HumanChannel(Protocol):
    """Human interaction channel (local CLI session, auto answerer, or ADO comments)."""

    def ask(self, session_id: str, request: HumanRequest) -> None: ...
    def collect(self, session_id: str) -> HumanResponse | None: ...
