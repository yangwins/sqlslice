"""Outlier detection: flags stages whose duration deviates significantly from the mean."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, stdev
from typing import List, Optional

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class OutlierStage:
    stage: Stage
    z_score: float
    deviation_ms: float

    def __repr__(self) -> str:
        return (
            f"OutlierStage(name={self.stage.name!r}, "
            f"duration_ms={self.stage.duration_ms:.2f}, "
            f"z_score={self.z_score:.2f})"
        )


@dataclass
class OutlierReport:
    query: str
    outliers: List[OutlierStage]
    mean_ms: float
    stdev_ms: float
    threshold: float

    @property
    def has_outliers(self) -> bool:
        return len(self.outliers) > 0

    def summary(self) -> str:
        lines = [
            f"Query : {self.query}",
            f"Mean  : {self.mean_ms:.2f} ms  StdDev: {self.stdev_ms:.2f} ms  Threshold (z): {self.threshold:.1f}",
        ]
        if not self.has_outliers:
            lines.append("No outlier stages detected.")
        else:
            lines.append(f"Outliers ({len(self.outliers)}):")
            for o in self.outliers:
                lines.append(
                    f"  {o.stage.name:<30} {o.stage.duration_ms:>10.2f} ms  z={o.z_score:+.2f}"
                )
        return "\n".join(lines)


class OutlierDetector:
    """Detect outlier stages using z-score analysis."""

    def __init__(self, threshold: float = 2.0) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        self.threshold = threshold

    def detect(self, result: ProfileResult) -> OutlierReport:
        stages = [s for s in result.stages if s.error is None]
        if len(stages) < 2:
            return OutlierReport(
                query=result.query,
                outliers=[],
                mean_ms=stages[0].duration_ms if stages else 0.0,
                stdev_ms=0.0,
                threshold=self.threshold,
            )
        durations = [s.duration_ms for s in stages]
        mu = mean(durations)
        sigma = stdev(durations)
        outliers: List[OutlierStage] = []
        for stage in stages:
            z = (stage.duration_ms - mu) / sigma if sigma > 0 else 0.0
            if abs(z) >= self.threshold:
                outliers.append(
                    OutlierStage(
                        stage=stage,
                        z_score=z,
                        deviation_ms=stage.duration_ms - mu,
                    )
                )
        outliers.sort(key=lambda o: abs(o.z_score), reverse=True)
        return OutlierReport(
            query=result.query,
            outliers=outliers,
            mean_ms=mu,
            stdev_ms=sigma,
            threshold=self.threshold,
        )
