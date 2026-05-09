"""Stage-level diff utilities for comparing two ProfileResults over time."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class StageTrend:
    stage_name: str
    durations: List[float] = field(default_factory=list)

    @property
    def mean(self) -> float:
        if not self.durations:
            return 0.0
        return sum(self.durations) / len(self.durations)

    @property
    def min(self) -> float:
        return min(self.durations, default=0.0)

    @property
    def max(self) -> float:
        return max(self.durations, default=0.0)

    @property
    def trend(self) -> str:
        """Return 'rising', 'falling', or 'stable' based on first vs last half."""
        if len(self.durations) < 2:
            return "stable"
        mid = len(self.durations) // 2
        first_half = sum(self.durations[:mid]) / mid
        second_half = sum(self.durations[mid:]) / (len(self.durations) - mid)
        delta = second_half - first_half
        if delta > first_half * 0.05:
            return "rising"
        if delta < -first_half * 0.05:
            return "falling"
        return "stable"

    def __repr__(self) -> str:
        return (
            f"StageTrend(stage={self.stage_name!r}, mean={self.mean:.4f}s, "
            f"trend={self.trend!r}, samples={len(self.durations)})"
        )


@dataclass
class DiffReport:
    query: str
    run_count: int
    stage_trends: List[StageTrend]
    errors: List[Optional[str]] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Query : {self.query}",
            f"Runs  : {self.run_count}",
            "-" * 40,
        ]
        for st in self.stage_trends:
            lines.append(
                f"  {st.stage_name:<20} mean={st.mean:.4f}s  "
                f"min={st.min:.4f}s  max={st.max:.4f}s  [{st.trend}]"
            )
        error_count = sum(1 for e in self.errors if e is not None)
        if error_count:
            lines.append(f"Errors: {error_count}/{self.run_count}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"DiffReport(query={self.query!r}, runs={self.run_count})"


class ProfileDiffer:
    """Accumulates multiple ProfileResult runs and produces a DiffReport."""

    def __init__(self) -> None:
        self._results: List[ProfileResult] = []

    def add(self, result: ProfileResult) -> None:
        if not isinstance(result, ProfileResult):
            raise TypeError("Expected a ProfileResult instance.")
        self._results.append(result)

    def diff(self) -> DiffReport:
        if not self._results:
            raise ValueError("No results to diff.")

        query = self._results[0].query
        trends: dict[str, StageTrend] = {}

        for result in self._results:
            for stage in result.stages:
                if stage.name not in trends:
                    trends[stage.name] = StageTrend(stage_name=stage.name)
                trends[stage.name].durations.append(stage.duration)

        errors = [r.error for r in self._results]

        return DiffReport(
            query=query,
            run_count=len(self._results),
            stage_trends=list(trends.values()),
            errors=errors,
        )
