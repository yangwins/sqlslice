"""Aggregator module: combines multiple ProfileResults into statistical summaries."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from statistics import mean, median, stdev

from sqlslice.profiler import ProfileResult


@dataclass
class StageStats:
    name: str
    count: int
    min_duration: float
    max_duration: float
    mean_duration: float
    median_duration: float
    stdev_duration: float

    def __repr__(self) -> str:
        return (
            f"StageStats({self.name!r}, mean={self.mean_duration:.4f}s, "
            f"min={self.min_duration:.4f}s, max={self.max_duration:.4f}s)"
        )


@dataclass
class AggregationReport:
    query: str
    run_count: int
    total_mean: float
    total_min: float
    total_max: float
    stage_stats: List[StageStats] = field(default_factory=list)
    error_count: int = 0

    def summary(self) -> str:
        lines = [
            f"Query      : {self.query}",
            f"Runs       : {self.run_count} (errors: {self.error_count})",
            f"Total mean : {self.total_mean:.4f}s",
            f"Total min  : {self.total_min:.4f}s",
            f"Total max  : {self.total_max:.4f}s",
            "",
            f"{'Stage':<25} {'Mean':>10} {'Min':>10} {'Max':>10} {'StdDev':>10}",
            "-" * 67,
        ]
        for s in self.stage_stats:
            lines.append(
                f"{s.name:<25} {s.mean_duration:>10.4f} {s.min_duration:>10.4f} "
                f"{s.max_duration:>10.4f} {s.stdev_duration:>10.4f}"
            )
        return "\n".join(lines)


class ProfileAggregator:
    """Aggregates multiple ProfileResult runs for the same query."""

    def __init__(self, query: Optional[str] = None):
        self._query = query
        self._results: List[ProfileResult] = []

    def add(self, result: ProfileResult) -> None:
        if self._query is None:
            self._query = result.query
        self._results.append(result)

    def aggregate(self) -> AggregationReport:
        if not self._results:
            raise ValueError("No results to aggregate.")

        successful = [r for r in self._results if r.error is None]
        error_count = len(self._results) - len(successful)
        totals = [r.total_duration for r in successful] if successful else [0.0]

        stage_map: Dict[str, List[float]] = {}
        for result in successful:
            for stage in result.stages:
                stage_map.setdefault(stage.name, []).append(stage.duration)

        stage_stats = [
            StageStats(
                name=name,
                count=len(durations),
                min_duration=min(durations),
                max_duration=max(durations),
                mean_duration=mean(durations),
                median_duration=median(durations),
                stdev_duration=stdev(durations) if len(durations) > 1 else 0.0,
            )
            for name, durations in stage_map.items()
        ]

        return AggregationReport(
            query=self._query or "",
            run_count=len(self._results),
            total_mean=mean(totals),
            total_min=min(totals),
            total_max=max(totals),
            stage_stats=stage_stats,
            error_count=error_count,
        )
