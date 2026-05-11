"""Heatmap module: visualises stage duration intensity across multiple runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from sqlslice.profiler import ProfileResult


@dataclass
class HeatCell:
    stage_name: str
    run_index: int
    duration_ms: float
    intensity: float  # 0.0 (coolest) .. 1.0 (hottest)

    def __repr__(self) -> str:
        return (
            f"HeatCell(stage={self.stage_name!r}, run={self.run_index}, "
            f"duration={self.duration_ms:.2f}ms, intensity={self.intensity:.2f})"
        )


@dataclass
class HeatmapReport:
    query: str
    cells: List[HeatCell] = field(default_factory=list)
    run_count: int = 0
    stage_names: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"Heatmap for: {self.query}", f"Runs: {self.run_count}"]
        for name in self.stage_names:
            row_cells = [c for c in self.cells if c.stage_name == name]
            bar = "".join(_intensity_char(c.intensity) for c in row_cells)
            lines.append(f"  {name:<24} {bar}")
        return "\n".join(lines)


def _intensity_char(intensity: float) -> str:
    if intensity < 0.25:
        return "░"
    if intensity < 0.5:
        return "▒"
    if intensity < 0.75:
        return "▓"
    return "█"


class QueryHeatmap:
    """Builds a heatmap from a sequence of ProfileResult objects."""

    def __init__(self, query: Optional[str] = None) -> None:
        self._query = query
        self._results: List[ProfileResult] = []

    def add(self, result: ProfileResult) -> None:
        if not isinstance(result, ProfileResult):
            raise TypeError("result must be a ProfileResult")
        self._results.append(result)

    def build(self) -> HeatmapReport:
        if not self._results:
            raise ValueError("No results added; cannot build heatmap.")

        query = self._query or self._results[0].query
        stage_names: List[str] = []
        seen: set = set()
        for r in self._results:
            for s in r.stages:
                if s.name not in seen:
                    stage_names.append(s.name)
                    seen.add(s.name)

        # per-stage min/max across all runs for normalisation
        stage_min: Dict[str, float] = {}
        stage_max: Dict[str, float] = {}
        for name in stage_names:
            durations = [
                s.duration_ms
                for r in self._results
                for s in r.stages
                if s.name == name
            ]
            stage_min[name] = min(durations)
            stage_max[name] = max(durations)

        cells: List[HeatCell] = []
        for run_idx, result in enumerate(self._results):
            for stage in result.stages:
                lo = stage_min[stage.name]
                hi = stage_max[stage.name]
                span = hi - lo
                intensity = (stage.duration_ms - lo) / span if span > 0 else 0.0
                cells.append(
                    HeatCell(
                        stage_name=stage.name,
                        run_index=run_idx,
                        duration_ms=stage.duration_ms,
                        intensity=intensity,
                    )
                )

        return HeatmapReport(
            query=query,
            cells=cells,
            run_count=len(self._results),
            stage_names=stage_names,
        )
