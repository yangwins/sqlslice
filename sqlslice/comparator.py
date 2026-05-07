"""Compare two ProfileResult objects to identify regressions or improvements."""

from dataclasses import dataclass
from typing import List, Optional
from sqlslice.profiler import ProfileResult, Stage


@dataclass
class StageDiff:
    stage_name: str
    baseline_duration: float
    current_duration: float

    @property
    def delta(self) -> float:
        return self.current_duration - self.baseline_duration

    @property
    def pct_change(self) -> Optional[float]:
        if self.baseline_duration == 0:
            return None
        return (self.delta / self.baseline_duration) * 100

    def __repr__(self) -> str:
        pct = f"{self.pct_change:+.1f}%" if self.pct_change is not None else "N/A"
        return (
            f"StageDiff(stage={self.stage_name!r}, "
            f"delta={self.delta:+.4f}s, change={pct})"
        )


@dataclass
class ComparisonReport:
    baseline: ProfileResult
    current: ProfileResult
    diffs: List[StageDiff]

    @property
    def total_delta(self) -> float:
        return self.current.total_duration - self.baseline.total_duration

    @property
    def is_regression(self) -> bool:
        return self.total_delta > 0

    def summary(self) -> str:
        lines = [
            f"Query: {self.current.query}",
            f"Baseline total : {self.baseline.total_duration:.4f}s",
            f"Current total  : {self.current.total_duration:.4f}s",
            f"Delta          : {self.total_delta:+.4f}s",
            "",
            "Stage breakdown:",
        ]
        for diff in self.diffs:
            pct = f"{diff.pct_change:+.1f}%" if diff.pct_change is not None else "N/A"
            lines.append(
                f"  {diff.stage_name:<20} {diff.delta:+.4f}s  ({pct})"
            )
        return "\n".join(lines)


class QueryComparator:
    def compare(self, baseline: ProfileResult, current: ProfileResult) -> ComparisonReport:
        """Compare two ProfileResult objects stage by stage."""
        baseline_map = {s.name: s.duration for s in baseline.stages}
        current_map = {s.name: s.duration for s in current.stages}

        all_names = list(dict.fromkeys(
            [s.name for s in baseline.stages] + [s.name for s in current.stages]
        ))

        diffs = [
            StageDiff(
                stage_name=name,
                baseline_duration=baseline_map.get(name, 0.0),
                current_duration=current_map.get(name, 0.0),
            )
            for name in all_names
        ]

        return ComparisonReport(baseline=baseline, current=current, diffs=diffs)
