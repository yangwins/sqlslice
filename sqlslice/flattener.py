"""Flattener: collapses nested or repeated stage names into a single merged view."""

from dataclasses import dataclass, field
from typing import List, Dict
from sqlslice.profiler import ProfileResult, Stage


@dataclass
class FlatStage:
    name: str
    total_duration_ms: float
    call_count: int

    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.call_count if self.call_count else 0.0

    def __repr__(self) -> str:
        return (
            f"FlatStage(name={self.name!r}, total_ms={self.total_duration_ms:.2f}, "
            f"calls={self.call_count}, avg_ms={self.avg_duration_ms():.2f})"
        )


@dataclass
class FlatReport:
    query: str
    flat_stages: List[FlatStage]
    original_stage_count: int

    def summary(self) -> str:
        lines = [
            f"Query : {self.query}",
            f"Stages: {len(self.flat_stages)} unique (from {self.original_stage_count} total)",
        ]
        for fs in sorted(self.flat_stages, key=lambda s: s.total_duration_ms, reverse=True):
            lines.append(
                f"  {fs.name}: {fs.total_duration_ms:.2f} ms total, "
                f"{fs.call_count} call(s), {fs.avg_duration_ms():.2f} ms avg"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"FlatReport(query={self.query!r}, unique_stages={len(self.flat_stages)}, "
            f"original_stages={self.original_stage_count})"
        )


class QueryFlattener:
    """Merges duplicate stage names within a ProfileResult."""

    def flatten(self, result: ProfileResult) -> FlatReport:
        if not isinstance(result, ProfileResult):
            raise TypeError("result must be a ProfileResult instance")

        buckets: Dict[str, FlatStage] = {}
        for stage in result.stages:
            name = stage.name
            if name not in buckets:
                buckets[name] = FlatStage(name=name, total_duration_ms=0.0, call_count=0)
            buckets[name].total_duration_ms += stage.duration_ms
            buckets[name].call_count += 1

        return FlatReport(
            query=result.query,
            flat_stages=list(buckets.values()),
            original_stage_count=len(result.stages),
        )
