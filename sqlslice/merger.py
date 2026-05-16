"""Merge multiple ProfileResults into a single unified result."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class MergeReport:
    query: str
    merged_stages: List[Stage]
    source_count: int
    total_duration_ms: float
    errors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Query : {self.query}",
            f"Sources merged : {self.source_count}",
            f"Stages : {len(self.merged_stages)}",
            f"Total duration : {self.total_duration_ms:.2f} ms",
        ]
        if self.errors:
            lines.append(f"Errors skipped : {len(self.errors)}")
            for e in self.errors:
                lines.append(f"  - {e}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"MergeReport(sources={self.source_count}, "
            f"stages={len(self.merged_stages)}, "
            f"total_ms={self.total_duration_ms:.2f})"
        )


class ProfileMerger:
    """Combine stages from multiple ProfileResult objects.

    Stages with the same name have their durations summed.  Results
    that carry an error string are skipped and recorded separately.
    """

    def __init__(self, query_name: Optional[str] = None) -> None:
        self.query_name = query_name

    def merge(self, results: List[ProfileResult]) -> MergeReport:
        if not results:
            raise ValueError("merge() requires at least one ProfileResult")

        errors: List[str] = []
        valid: List[ProfileResult] = []
        for r in results:
            if r.error:
                errors.append(r.error)
            else:
                valid.append(r)

        query = self.query_name or (valid[0].query if valid else results[0].query)

        # Sum durations per stage name, preserving first-seen order
        totals: dict[str, float] = {}
        for r in valid:
            for stage in r.stages:
                totals[stage.name] = totals.get(stage.name, 0.0) + stage.duration_ms

        merged_stages = [
            Stage(name=name, duration_ms=dur) for name, dur in totals.items()
        ]
        total_duration = sum(s.duration_ms for s in merged_stages)

        return MergeReport(
            query=query,
            merged_stages=merged_stages,
            source_count=len(results),
            total_duration_ms=total_duration,
            errors=errors,
        )
