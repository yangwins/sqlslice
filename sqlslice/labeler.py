"""Stage labeler: attach severity labels to profiling stages based on duration thresholds."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from sqlslice.profiler import ProfileResult, Stage

LABEL_OK = "ok"
LABEL_SLOW = "slow"
LABEL_CRITICAL = "critical"


@dataclass
class LabeledStage:
    stage: Stage
    label: str

    def __repr__(self) -> str:
        return f"LabeledStage(name={self.stage.name!r}, duration_ms={self.stage.duration_ms:.2f}, label={self.label!r})"


@dataclass
class LabelReport:
    query: str
    labeled_stages: List[LabeledStage] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"Query: {self.query}"]
        for ls in self.labeled_stages:
            lines.append(f"  [{ls.label.upper():8s}] {ls.stage.name}: {ls.stage.duration_ms:.2f} ms")
        counts = self._label_counts()
        lines.append(
            f"Labels: ok={counts[LABEL_OK]}, slow={counts[LABEL_SLOW]}, critical={counts[LABEL_CRITICAL]}"
        )
        return "\n".join(lines)

    def _label_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {LABEL_OK: 0, LABEL_SLOW: 0, LABEL_CRITICAL: 0}
        for ls in self.labeled_stages:
            counts[ls.label] = counts.get(ls.label, 0) + 1
        return counts

    def by_label(self, label: str) -> List[LabeledStage]:
        return [ls for ls in self.labeled_stages if ls.label == label]

    def __repr__(self) -> str:
        return f"LabelReport(query={self.query!r}, stages={len(self.labeled_stages)})"


class StageLabeler:
    """Attach ok/slow/critical labels to each stage in a ProfileResult."""

    def __init__(self, slow_ms: float = 100.0, critical_ms: float = 500.0) -> None:
        if slow_ms <= 0:
            raise ValueError("slow_ms must be positive")
        if critical_ms <= slow_ms:
            raise ValueError("critical_ms must be greater than slow_ms")
        self.slow_ms = slow_ms
        self.critical_ms = critical_ms

    def label(self, result: ProfileResult) -> LabelReport:
        labeled: List[LabeledStage] = []
        for stage in result.stages:
            if stage.duration_ms >= self.critical_ms:
                lbl = LABEL_CRITICAL
            elif stage.duration_ms >= self.slow_ms:
                lbl = LABEL_SLOW
            else:
                lbl = LABEL_OK
            labeled.append(LabeledStage(stage=stage, label=lbl))
        return LabelReport(query=result.query, labeled_stages=labeled)
