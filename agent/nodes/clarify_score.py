"""Clarification scoring node: scores ticket, absorbs comment answers, generates questions."""

import json
import logging
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from agent.core.protocols import LLMClient
from agent.core.state import RunState
from agent.rubric.scorer import load_rubric

logger = logging.getLogger(__name__)


class ClarifyScoreOutput(BaseModel):
    """Schema for LLM rubric evaluation."""

    score: float
    reasoning: str = ""
    questions: list[str] = Field(default_factory=list)


def extract_answers_from_comments(comments_text: list[str]) -> dict[str, str]:
    """Extract answers provided directly in work item comments."""
    answers: dict[str, str] = {}
    answer_idx = 1
    for body in comments_text:
        # Match common clarification answer patterns
        # e.g. "Answer: ...", "Answers: ...", "Clarification: ..."
        match = re.search(r"(?:answer|clarification)s?:\s*(.+)", body, re.IGNORECASE | re.DOTALL)
        if match:
            ans_text = match.group(1).strip()
            answers[f"comment_answer_{answer_idx}"] = ans_text
            answer_idx += 1
        elif "yes" in body.lower() or "no" in body.lower() or "default" in body.lower():
            # Absorbs short direct replies
            answers[f"comment_answer_{answer_idx}"] = body.strip()
            answer_idx += 1

    return answers


def clarify_score_node(
    state: RunState,
    llm: LLMClient,
    rubric_path: Path | None = None,
) -> dict[str, Any]:
    """Score the ticket against the rubric, absorbing answers from comments first."""
    if not state.ticket:
        raise ValueError("Cannot score ticket: state.ticket is missing.")

    rubric = load_rubric(rubric_path)

    # 1. Harvest answers already present in comments
    comment_bodies = [c.body for c in state.ticket.comments]
    absorbed_answers = extract_answers_from_comments(comment_bodies)
    all_answers = {**state.clarification_answers, **absorbed_answers}

    # 2. Score ticket with LLM
    prompt = (
        f"Evaluate this work item against our specification rubric (threshold "
        f"{rubric.threshold}/10).\n\n"
        f"Title: {state.ticket.title}\n"
        f"Description: {state.ticket.description}\n"
        f"Acceptance Criteria: {state.ticket.acceptance_criteria}\n"
        f"Existing Clarifications/Answers: {all_answers}\n\n"
        "Output JSON with:\n"
        "- score: float between 0.0 and 10.0\n"
        "- reasoning: brief explanation\n"
        "- questions: list of 3-5 specific questions only if there are critical gaps remaining\n"
    )

    llm_res = llm.complete(
        role="clarify",
        messages=[{"role": "user", "content": prompt}],
        schema=ClarifyScoreOutput,
        session_id=f"ado-{state.ticket_id}",
    )

    score = 8.0
    questions: list[str] = []
    if llm_res.parsed and isinstance(llm_res.parsed, ClarifyScoreOutput):
        score = llm_res.parsed.score
        questions = llm_res.parsed.questions
    elif llm_res.text:
        try:
            data = json.loads(llm_res.text)
            score = float(data.get("score", 8.0))
            questions = [str(q) for q in data.get("questions", [])]
        except Exception:
            pass

    # If ticket has absorbed answers or exceeds threshold, route to impact analysis
    has_gaps = score < rubric.threshold and len(questions) > 0

    if not has_gaps:
        return {
            "rubric_score": score,
            "clarification_answers": all_answers,
            "clarification_questions": [],
            "stage": "impact",
            "messages": [
                *state.messages,
                f"Clarification passed with rubric score {score:.1f}/{rubric.threshold}",
            ],
        }

    return {
        "rubric_score": score,
        "clarification_answers": all_answers,
        "clarification_questions": questions,
        "stage": "clarify",
        "messages": [
            *state.messages,
            (
                f"Ticket needs clarification (score {score:.1f}/{rubric.threshold}), "
                f"generated {len(questions)} questions."
            ),
        ],
    }
