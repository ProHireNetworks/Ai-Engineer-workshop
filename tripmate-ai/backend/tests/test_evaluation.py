"""
TripMate AI - Benchmark Evaluation Tests
Tests evaluation metrics aggregation and runner execution on sample benchmark cases.
"""

import pytest
from app.evaluation.metrics import EvaluationSummary, TestCaseEvaluation
from app.evaluation.runner import EvaluationRunner


def test_metrics_aggregation_math():
    """Verify statistical aggregation of completeness, budget accuracy, and latency."""
    res1 = TestCaseEvaluation(
        case_id="tc_1",
        case_name="Case 1",
        category="cat_a",
        passed=True,
        status="SUCCESS",
        completeness_score=1.0,
        budget_accuracy_score=0.95,
        latency_ms=100.0,
        tokens_used=500,
        estimated_cost_usd=0.00015,
    )
    res2 = TestCaseEvaluation(
        case_id="tc_2",
        case_name="Case 2",
        category="cat_b",
        passed=False,
        status="FAILED",
        completeness_score=0.5,
        budget_accuracy_score=0.40,
        latency_ms=200.0,
        tokens_used=300,
        estimated_cost_usd=0.00009,
    )

    summary = EvaluationSummary.aggregate([res1, res2])
    assert summary.total_cases == 2
    assert summary.passed_cases == 1
    assert summary.failed_cases == 1
    assert summary.pass_rate_pct == 50.0
    assert summary.avg_completeness_score == 0.75
    assert summary.avg_budget_accuracy_score == 0.675
    assert summary.avg_latency_ms == 150.0
    assert summary.total_tokens == 800
    assert round(summary.total_cost_usd, 5) == 0.00024


@pytest.mark.asyncio
async def test_evaluation_runner_subset():
    """Test evaluation runner on a subset of benchmark cases."""
    runner = EvaluationRunner()
    cases = runner.load_test_cases(limit=3)
    assert len(cases) == 3

    summary = await runner.run_benchmark(limit=3, output_report=False)
    assert summary.total_cases == 3
    assert summary.pass_rate_pct >= 66.0
    assert len(summary.case_evaluations) == 3
    for eval_case in summary.case_evaluations:
        assert eval_case.latency_ms >= 0.0
        assert eval_case.completeness_score >= 0.0

