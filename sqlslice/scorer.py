"""Stage-by-stage performance scorer that assigns 0-100 scores based on duration budgets."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class ScoredStage:
    stage: Stage
    score: int  # 0 (worst) – 100 (best)
    grade: str

    def __repr__(self) -> str:
        return (
            f"ScoredStage(name={self.stage.name!r}, "
            f"duration_ms={self.stage.duration_ms:.2f}, "
            f"score={self.score}, grade={self.grade!r})"
        )


@dataclass
class ScoreReport:
    query: str
    scored_stages: List[ScoredStage]
    overall_score: int
    overall_grade: str

    def summary(self) -> str:
        lines = [
            f"Query : {self.query}",
            f"Overall: {self.overall_score}/100 ({self.overall_grade})",
            "-" * 48,
        ]
        for ss in self.scored_stages:
            lines.append(
                f"  {ss.stage.name:<24} {ss.stage.duration_ms:>8.2f} ms  "
                f"{ss.score:>3}/100  {ss.grade}"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"ScoreReport(query={self.query!r}, "
            f"overall_score={self.overall_score}, "
            f"overall_grade={self.overall_grade!r})"
        )


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 55:
        return "C"
    if score >= 35:
        return "D"
    return "F"


class QueryScorer:
    """Score each stage relative to a *budget_ms* ceiling.

    A stage that completes in 0 ms scores 100; a stage that meets or
    exceeds *budget_ms* scores 0.  Intermediate values are linear.
    """

    def __init__(self, budget_ms: float = 500.0) -> None:
        if not isinstance(budget_ms, (int, float)) or budget_ms <= 0:
            raise ValueError("budget_ms must be a positive number.")
        self.budget_ms = float(budget_ms)

    def score(self, result: ProfileResult) -> ScoreReport:
        if not result.stages:
            raise ValueError("ProfileResult has no stages to score.")

        scored: List[ScoredStage] = []
        for stage in result.stages:
            raw = max(0.0, 1.0 - stage.duration_ms / self.budget_ms)
            s = round(raw * 100)
            scored.append(ScoredStage(stage=stage, score=s, grade=_grade(s)))

        overall = round(sum(ss.score for ss in scored) / len(scored))
        return ScoreReport(
            query=result.query,
            scored_stages=scored,
            overall_score=overall,
            overall_grade=_grade(overall),
        )
