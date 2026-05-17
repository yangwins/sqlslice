"""Group profiling results by a stage name pattern or custom key function."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class GroupedBucket:
    """A named bucket holding one or more ProfileResults."""

    key: str
    results: List[ProfileResult] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.results)

    @property
    def total_duration_ms(self) -> float:
        return sum(
            sum(s.duration_ms for s in r.stages) for r in self.results
        )

    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.count if self.count else 0.0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"GroupedBucket(key={self.key!r}, count={self.count}, "
            f"avg_ms={self.avg_duration_ms:.2f})"
        )


@dataclass
class GroupReport:
    """Result of a grouping operation."""

    query: str
    buckets: List[GroupedBucket]

    @property
    def bucket_count(self) -> int:
        return len(self.buckets)

    def get(self, key: str) -> Optional[GroupedBucket]:
        """Return the bucket with the given key, or None."""
        for b in self.buckets:
            if b.key == key:
                return b
        return None

    def summary(self) -> str:
        lines = [f"Query : {self.query}", f"Groups: {self.bucket_count}"]
        for b in sorted(self.buckets, key=lambda x: x.total_duration_ms, reverse=True):
            lines.append(
                f"  [{b.key}] runs={b.count} "
                f"total={b.total_duration_ms:.2f}ms "
                f"avg={b.avg_duration_ms:.2f}ms"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:  # pragma: no cover
        return f"GroupReport(query={self.query!r}, buckets={self.bucket_count})"


class ProfileGrouper:
    """Group a list of ProfileResults into named buckets."""

    def __init__(
        self,
        key_fn: Optional[Callable[[ProfileResult], str]] = None,
    ) -> None:
        """Parameters
        ----------
        key_fn:
            Callable that maps a ProfileResult to a bucket key string.
            Defaults to grouping by the query string itself.
        """
        self._key_fn: Callable[[ProfileResult], str] = key_fn or (
            lambda r: r.query
        )

    def group(self, results: List[ProfileResult]) -> GroupReport:
        if not results:
            raise ValueError("results list must not be empty")

        buckets: Dict[str, GroupedBucket] = {}
        for r in results:
            key = self._key_fn(r)
            if key not in buckets:
                buckets[key] = GroupedBucket(key=key)
            buckets[key].results.append(r)

        query = results[0].query
        return GroupReport(query=query, buckets=list(buckets.values()))
