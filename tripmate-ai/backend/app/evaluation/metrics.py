"""
TripMate AI - Agent Evaluation Metrics
Defines evaluation scoring, token accounting, latency metrics, and aggregated summaries.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TestCaseEvaluation(BaseModel):
    """Detailed score report for an individual benchmark test case."""

    __test__ = False

    case_id: str
    case_name: str
    category: str
    passed: bool
    status: str
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Completeness of required trip components")
    budget_accuracy_score: float = Field(..., ge=0.0, le=1.0, description="Variance between target and calculated budget")
    tool_success_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    latency_ms: float = Field(..., ge=0.0)
    tokens_used: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)
    errors: List[str] = Field(default_factory=list)


class EvaluationSummary(BaseModel):
    """Aggregated performance, accuracy, latency, and cost summary across all test cases."""

    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate_pct: float
    avg_completeness_score: float
    avg_budget_accuracy_score: float
    avg_latency_ms: float
    p95_latency_ms: float
    total_tokens: int
    total_cost_usd: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    case_evaluations: List[TestCaseEvaluation] = Field(default_factory=list)

    @classmethod
    def aggregate(cls, results: List[TestCaseEvaluation]) -> "EvaluationSummary":
        total = len(results)
        if total == 0:
            return cls(
                total_cases=0,
                passed_cases=0,
                failed_cases=0,
                pass_rate_pct=0.0,
                avg_completeness_score=0.0,
                avg_budget_accuracy_score=0.0,
                avg_latency_ms=0.0,
                p95_latency_ms=0.0,
                total_tokens=0,
                total_cost_usd=0.0,
            )

        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        pass_rate = round((passed / total) * 100, 2)

        avg_comp = round(sum(r.completeness_score for r in results) / total, 3)
        avg_budget = round(sum(r.budget_accuracy_score for r in results) / total, 3)
        avg_lat = round(sum(r.latency_ms for r in results) / total, 2)

        latencies = sorted(r.latency_ms for r in results)
        p95_idx = int(total * 0.95)
        p95_lat = round(latencies[min(p95_idx, total - 1)], 2)

        total_tok = sum(r.tokens_used for r in results)
        total_cost = round(sum(r.estimated_cost_usd for r in results), 6)

        return cls(
            total_cases=total,
            passed_cases=passed,
            failed_cases=failed,
            pass_rate_pct=pass_rate,
            avg_completeness_score=avg_comp,
            avg_budget_accuracy_score=avg_budget,
            avg_latency_ms=avg_lat,
            p95_latency_ms=p95_lat,
            total_tokens=total_tok,
            total_cost_usd=total_cost,
            case_evaluations=results,
        )
