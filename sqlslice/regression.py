"""Regression detector: flags stages that have gotten slower across runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class RegressionFlag:
    stage_name: str
    baseline_ms: float
    current_ms: float
    delta_ms: float
    pct_change: float

    def __repr__(self) -> str:
        return (
            f"RegressionFlag(stage={self.stage_name!r}, "
            f"baseline={self.baseline_ms:.2f}ms, "
            f"current={self.current_ms:.2f}ms, "
            f"+{self.delta_ms:.2f}ms / +{self.pct_change:.1f}%)"
        )


@dataclass
class RegressionReport:
    query: str
    flags: List[RegressionFlag] = field(default_factory=list)
    threshold_pct: float = 10.0

    @property
    def has_regressions(self) -> bool:
        return len(self.flags) > 0

    def summary(self) -> str:
        if not self.has_regressions:
            return f"[RegressionReport] query={self.query!r} — no regressions detected"
        lines = [f"[RegressionReport] query={self.query!r} — {len(self.flags)} regression(s):"]
        for f in self.flags:
            lines.append(
                f"  {f.stage_name}: {f.baseline_ms:.2f}ms -> {f.current_ms:.2f}ms "
                f"(+{f.delta_ms:.2f}ms, +{f.pct_change:.1f}%)"
            )
        return "\n".join(lines)


class RegressionDetector:
    """Compare a baseline ProfileResult against a current one and flag regressions."""

    def __init__(self, threshold_pct: float = 10.0) -> None:
        if threshold_pct <= 0:
            raise ValueError("threshold_pct must be positive")
        self.threshold_pct = threshold_pct

    def detect(
        self, baseline: ProfileResult, current: ProfileResult
    ) -> RegressionReport:
        baseline_map = {s.name: s.duration_ms for s in baseline.stages}
        current_map = {s.name: s.duration_ms for s in current.stages}

        flags: List[RegressionFlag] = []
        for name, cur_ms in current_map.items():
            if name not in baseline_map:
                continue
            base_ms = baseline_map[name]
            if base_ms <= 0:
                continue
            delta = cur_ms - base_ms
            pct = (delta / base_ms) * 100.0
            if pct >= self.threshold_pct:
                flags.append(
                    RegressionFlag(
                        stage_name=name,
                        baseline_ms=base_ms,
                        current_ms=cur_ms,
                        delta_ms=delta,
                        pct_change=pct,
                    )
                )

        return RegressionReport(
            query=current.query,
            flags=flags,
            threshold_pct=self.threshold_pct,
        )
