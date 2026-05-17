"""Stage trimmer: removes stages below a minimum duration threshold."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class TrimReport:
    query: str
    kept: List[Stage]
    removed: List[Stage]
    min_duration_ms: float

    @property
    def kept_count(self) -> int:
        return len(self.kept)

    @property
    def removed_count(self) -> int:
        return len(self.removed)

    @property
    def total_kept_ms(self) -> float:
        return sum(s.duration_ms for s in self.kept)

    def summary(self) -> str:
        lines = [
            f"Query : {self.query}",
            f"Min   : {self.min_duration_ms:.2f} ms",
            f"Kept  : {self.kept_count} stage(s)  ({self.total_kept_ms:.2f} ms)",
            f"Removed: {self.removed_count} stage(s)",
        ]
        if self.removed:
            names = ", ".join(s.name for s in self.removed)
            lines.append(f"  -> {names}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"TrimReport(kept={self.kept_count}, removed={self.removed_count}, "
            f"min_duration_ms={self.min_duration_ms})"
        )


class StageTrimmer:
    """Removes stages whose duration is strictly below *min_duration_ms*."""

    def __init__(self, min_duration_ms: float = 1.0) -> None:
        if not isinstance(min_duration_ms, (int, float)):
            raise TypeError("min_duration_ms must be a number")
        if min_duration_ms <= 0:
            raise ValueError("min_duration_ms must be positive")
        self.min_duration_ms = float(min_duration_ms)

    def trim(self, result: ProfileResult) -> TrimReport:
        """Return a TrimReport partitioning stages by the minimum threshold."""
        if not isinstance(result, ProfileResult):
            raise TypeError("result must be a ProfileResult")

        kept: List[Stage] = []
        removed: List[Stage] = []

        for stage in result.stages:
            if stage.duration_ms >= self.min_duration_ms:
                kept.append(stage)
            else:
                removed.append(stage)

        return TrimReport(
            query=result.query,
            kept=kept,
            removed=removed,
            min_duration_ms=self.min_duration_ms,
        )
