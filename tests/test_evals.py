from pathlib import Path

from evals.dataset import BENCHMARK_CASES
from evals.runner import evaluate_ticket


def test_eval_benchmark_suite(tmp_path: Path) -> None:
    """Verify that benchmark evaluation harness runs and scores all archetypes."""
    # Run a sample from each archetype
    sample_cases = [
        BENCHMARK_CASES[0],  # localized_bug (4966)
        BENCHMARK_CASES[3],  # vague_spec (4969)
        BENCHMARK_CASES[6],  # api_contract (11595)
        BENCHMARK_CASES[9],  # cross_cutting (11680)
    ]

    for case in sample_cases:
        res = evaluate_ticket(case, tmp_path)
        assert res["outcome"] == "PASS"
        assert res["pr_created"] is True
        assert res["clarify_match"] is True
