"""Query deduplicator: groups ProfileResults by normalized fingerprint and collapses duplicates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from sqlslice.profiler import ProfileResult
from sqlslice.normalizer import QueryNormalizer


@dataclass
class DedupGroup:
    fingerprint: str
    canonical_query: str
    results: List[ProfileResult] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.results)

    @property
    def total_duration_ms(self) -> float:
        return sum(r.total_duration_ms for r in self.results)

    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.count if self.count else 0.0

    def __repr__(self) -> str:
        return (
            f"DedupGroup(fingerprint={self.fingerprint!r}, "
            f"count={self.count}, avg_ms={self.avg_duration_ms:.2f})"
        )


@dataclass
class DeduplicationReport:
    groups: List[DedupGroup]

    @property
    def group_count(self) -> int:
        return len(self.groups)

    @property
    def total_results(self) -> int:
        return sum(g.count for g in self.groups)

    def summary(self) -> str:
        lines = [f"Deduplication Report — {self.group_count} unique query pattern(s)"]
        for g in sorted(self.groups, key=lambda x: x.avg_duration_ms, reverse=True):
            lines.append(
                f"  [{g.fingerprint[:12]}...]  count={g.count}  "
                f"avg={g.avg_duration_ms:.2f}ms  total={g.total_duration_ms:.2f}ms"
            )
            lines.append(f"    Query: {g.canonical_query[:80]}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"DeduplicationReport(groups={self.group_count}, results={self.total_results})"


class QueryDeduplicator:
    """Groups multiple ProfileResults by their normalized query fingerprint."""

    def __init__(self) -> None:
        self._normalizer = QueryNormalizer()

    def deduplicate(self, results: List[ProfileResult]) -> DeduplicationReport:
        if not results:
            raise ValueError("results list must not be empty")

        groups: Dict[str, DedupGroup] = {}
        for result in results:
            normalized = self._normalizer.normalize(result.query)
            fp = normalized.fingerprint
            if fp not in groups:
                groups[fp] = DedupGroup(
                    fingerprint=fp,
                    canonical_query=result.query,
                )
            groups[fp].results.append(result)

        return DeduplicationReport(groups=list(groups.values()))
