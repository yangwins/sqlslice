"""Threshold checker: flags stages and queries that exceed configurable time limits."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class ThresholdViolation:
    stage_name: str
    duration_ms: float
    limit_ms: float

    @property
    def excess_ms(self) -> float:
        return self.duration_ms - self.limit_ms

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ThresholdViolation(stage={self.stage_name!r}, "
            f"duration={self.duration_ms:.2f}ms, limit={self.limit_ms:.2f}ms, "
            f"excess={self.excess_ms:.2f}ms)"
        )


@dataclass
class ThresholdReport:
    query: str
    total_duration_ms: float
    total_limit_ms: Optional[float]
    violations: List[ThresholdViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations) or (
            self.total_limit_ms is not None
            and self.total_duration_ms > self.total_limit_ms
        )

    @property
    def total_exceeded(self) -> bool:
        return (
            self.total_limit_ms is not None
            and self.total_duration_ms > self.total_limit_ms
        )

    def summary(self) -> str:
        lines = [f"Query : {self.query}"]
        lines.append(f"Total : {self.total_duration_ms:.2f}ms")
        if self.total_limit_ms is not None:
            status = "EXCEEDED" if self.total_exceeded else "ok"
            lines.append(f"Limit : {self.total_limit_ms:.2f}ms [{status}]")
        if self.violations:
            lines.append("Stage violations:")
            for v in self.violations:
                lines.append(
                    f"  {v.stage_name}: {v.duration_ms:.2f}ms > {v.limit_ms:.2f}ms "
                    f"(+{v.excess_ms:.2f}ms)"
                )
        elif not self.total_exceeded:
            lines.append("No threshold violations.")
        return "\n".join(lines)


class ThresholdChecker:
    """Check a ProfileResult against per-stage and total duration thresholds."""

    def __init__(
        self,
        stage_limits: Optional[dict] = None,
        total_limit_ms: Optional[float] = None,
    ) -> None:
        if total_limit_ms is not None and total_limit_ms <= 0:
            raise ValueError("total_limit_ms must be positive")
        self.stage_limits: dict = stage_limits or {}
        self.total_limit_ms = total_limit_ms

    def check(self, result: ProfileResult) -> ThresholdReport:
        violations: List[ThresholdViolation] = []
        for stage in result.stages:
            limit = self.stage_limits.get(stage.name)
            if limit is not None and stage.duration_ms > limit:
                violations.append(
                    ThresholdViolation(
                        stage_name=stage.name,
                        duration_ms=stage.duration_ms,
                        limit_ms=limit,
                    )
                )
        return ThresholdReport(
            query=result.query,
            total_duration_ms=result.total_duration_ms,
            total_limit_ms=self.total_limit_ms,
            violations=violations,
        )
