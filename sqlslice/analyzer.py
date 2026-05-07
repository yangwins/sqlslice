"""Analyzer module for identifying bottlenecks in SQL query profiles."""

from dataclasses import dataclass, field
from typing import List, Optional
from sqlslice.profiler import ProfileResult, Stage


@dataclass
class Bottleneck:
    stage: Stage
    pct_of_total: float
    is_slowest: bool = False

    def __repr__(self) -> str:
        flag = " [SLOWEST]" if self.is_slowest else ""
        return (
            f"Bottleneck(stage={self.stage.name!r}, "
            f"duration={self.stage.duration_ms:.2f}ms, "
            f"pct={self.pct_of_total:.1f}%{flag})"
        )


@dataclass
class AnalysisReport:
    query: str
    bottlenecks: List[Bottleneck] = field(default_factory=list)
    total_duration_ms: float = 0.0
    slowest_stage: Optional[Stage] = None
    error: Optional[str] = None

    def summary(self) -> str:
        if self.error:
            return f"Analysis failed: {self.error}"
        lines = [
            f"Query: {self.query}",
            f"Total: {self.total_duration_ms:.2f}ms",
            "Bottlenecks:",
        ]
        for b in self.bottlenecks:
            lines.append(f"  {b}")
        return "\n".join(lines)


class QueryAnalyzer:
    """Analyzes a ProfileResult to surface bottleneck stages."""

    def __init__(self, threshold_pct: float = 20.0):
        """
        Args:
            threshold_pct: Stages consuming at least this percentage of total
                           duration are flagged as bottlenecks.
        """
        if not (0 < threshold_pct <= 100):
            raise ValueError("threshold_pct must be between 0 and 100")
        self.threshold_pct = threshold_pct

    def analyze(self, result: ProfileResult) -> AnalysisReport:
        """Return an AnalysisReport for the given ProfileResult."""
        report = AnalysisReport(
            query=result.query,
            total_duration_ms=result.total_duration_ms,
            error=result.error,
        )

        if result.error or not result.stages:
            return report

        slowest = max(result.stages, key=lambda s: s.duration_ms)
        report.slowest_stage = slowest

        for stage in result.stages:
            pct = (
                (stage.duration_ms / result.total_duration_ms) * 100
                if result.total_duration_ms > 0
                else 0.0
            )
            if pct >= self.threshold_pct:
                report.bottlenecks.append(
                    Bottleneck(
                        stage=stage,
                        pct_of_total=pct,
                        is_slowest=(stage is slowest),
                    )
                )

        report.bottlenecks.sort(key=lambda b: b.pct_of_total, reverse=True)
        return report
