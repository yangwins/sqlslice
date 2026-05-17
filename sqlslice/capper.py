"""Stage duration capper — clamps stage timings to a configurable ceiling."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class CappedStage:
    name: str
    original_ms: float
    capped_ms: float
    was_capped: bool

    def __repr__(self) -> str:
        flag = " [CAPPED]" if self.was_capped else ""
        return f"CappedStage({self.name!r}, original={self.original_ms:.2f}ms, capped={self.capped_ms:.2f}ms{flag})"


@dataclass
class CapReport:
    query: str
    ceiling_ms: float
    stages: List[CappedStage]

    @property
    def capped_count(self) -> int:
        return sum(1 for s in self.stages if s.was_capped)

    @property
    def total_original_ms(self) -> float:
        return sum(s.original_ms for s in self.stages)

    @property
    def total_capped_ms(self) -> float:
        return sum(s.capped_ms for s in self.stages)

    def summary(self) -> str:
        lines = [
            f"Query : {self.query}",
            f"Ceiling: {self.ceiling_ms:.2f} ms",
            f"Stages : {len(self.stages)} ({self.capped_count} capped)",
            f"Total  : {self.total_original_ms:.2f} ms -> {self.total_capped_ms:.2f} ms",
            "",
        ]
        for s in self.stages:
            marker = "*" if s.was_capped else " "
            lines.append(f"  {marker} {s.name}: {s.original_ms:.2f} ms -> {s.capped_ms:.2f} ms")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"CapReport(query={self.query!r}, ceiling={self.ceiling_ms:.2f}ms, capped={self.capped_count}/{len(self.stages)})"


class StageCapper:
    """Clamp each stage duration to *ceiling_ms*."""

    def __init__(self, ceiling_ms: float) -> None:
        if not isinstance(ceiling_ms, (int, float)):
            raise TypeError("ceiling_ms must be a number")
        if ceiling_ms <= 0:
            raise ValueError("ceiling_ms must be positive")
        self._ceiling = float(ceiling_ms)

    def cap(self, result: ProfileResult) -> CapReport:
        if not isinstance(result, ProfileResult):
            raise TypeError("result must be a ProfileResult")
        capped_stages: List[CappedStage] = []
        for stage in result.stages:
            original = stage.duration_ms
            capped = min(original, self._ceiling)
            capped_stages.append(
                CappedStage(
                    name=stage.name,
                    original_ms=original,
                    capped_ms=capped,
                    was_capped=original > self._ceiling,
                )
            )
        return CapReport(
            query=result.query,
            ceiling_ms=self._ceiling,
            stages=capped_stages,
        )
