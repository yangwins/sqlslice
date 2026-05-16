"""Stage-level summary statistics for a ProfileResult."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class StageSummary:
    """Aggregated summary for a single stage across all stages in a result."""

    name: str
    duration_ms: float
    pct_of_total: float

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"StageSummary(name={self.name!r}, "
            f"duration_ms={self.duration_ms:.3f}, "
            f"pct_of_total={self.pct_of_total:.1f}%)"
        )


@dataclass
class SummaryReport:
    """Full summary report derived from a ProfileResult."""

    query: str
    total_ms: float
    stage_summaries: List[StageSummary]

    def summary(self) -> str:
        lines = [
            f"Query   : {self.query}",
            f"Total   : {self.total_ms:.3f} ms",
            "-" * 44,
        ]
        for s in self.stage_summaries:
            lines.append(
                f"  {s.name:<20} {s.duration_ms:>9.3f} ms  ({s.pct_of_total:5.1f}%)"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SummaryReport(query={self.query!r}, "
            f"total_ms={self.total_ms:.3f}, "
            f"stages={len(self.stage_summaries)})"
        )


class QuerySummarizer:
    """Builds a SummaryReport from a ProfileResult."""

    def build(self, result: ProfileResult) -> SummaryReport:
        """Return a SummaryReport for *result*.

        Raises
        ------
        ValueError
            If *result* has no stages.
        """
        if not isinstance(result, ProfileResult):
            raise TypeError(f"Expected ProfileResult, got {type(result).__name__}")

        stages: List[Stage] = result.stages
        if not stages:
            raise ValueError("ProfileResult contains no stages to summarise.")

        total_ms: float = sum(s.duration_ms for s in stages)

        summaries = [
            StageSummary(
                name=s.name,
                duration_ms=s.duration_ms,
                pct_of_total=(s.duration_ms / total_ms * 100) if total_ms > 0 else 0.0,
            )
            for s in stages
        ]

        return SummaryReport(
            query=result.query,
            total_ms=total_ms,
            stage_summaries=summaries,
        )
