"""Batch profiling: run multiple queries and collect results together."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from sqlslice.profiler import ProfileResult, QueryProfiler


@dataclass
class BatchEntry:
    name: str
    query: str
    result: Optional[ProfileResult] = None
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.result is not None and self.result.error is None

    def __repr__(self) -> str:
        status = "ok" if self.succeeded else "error"
        return f"BatchEntry(name={self.name!r}, status={status})"


@dataclass
class BatchReport:
    entries: List[BatchEntry]
    query: str = "<batch>"

    @property
    def total_count(self) -> int:
        return len(self.entries)

    @property
    def success_count(self) -> int:
        return sum(1 for e in self.entries if e.succeeded)

    @property
    def failure_count(self) -> int:
        return self.total_count - self.success_count

    @property
    def total_duration_ms(self) -> float:
        return sum(
            e.result.total_duration_ms
            for e in self.entries
            if e.result is not None
        )

    def summary(self) -> str:
        lines = [
            f"Batch Report — {self.total_count} queries",
            f"  Succeeded : {self.success_count}",
            f"  Failed    : {self.failure_count}",
            f"  Total ms  : {self.total_duration_ms:.2f}",
        ]
        for entry in self.entries:
            tag = "✓" if entry.succeeded else "✗"
            dur = (
                f"{entry.result.total_duration_ms:.2f} ms"
                if entry.result
                else entry.error or "no result"
            )
            lines.append(f"  [{tag}] {entry.name}: {dur}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"BatchReport(total={self.total_count}, "
            f"success={self.success_count}, "
            f"failed={self.failure_count})"
        )


class QueryBatcher:
    """Run a list of named queries through a profiler and collect batch results."""

    def __init__(self, profiler: QueryProfiler) -> None:
        if profiler is None:
            raise ValueError("profiler must not be None")
        self._profiler = profiler

    def run(
        self,
        queries: List[tuple[str, str]],
        on_entry: Optional[Callable[[BatchEntry], None]] = None,
    ) -> BatchReport:
        """Run each (name, query) pair and return a BatchReport.

        Args:
            queries: List of (name, sql) tuples.
            on_entry: Optional callback invoked after each entry completes.
        """
        if not queries:
            raise ValueError("queries list must not be empty")

        entries: List[BatchEntry] = []
        for name, sql in queries:
            try:
                result = self._profiler.profile(sql)
                entry = BatchEntry(name=name, query=sql, result=result)
            except Exception as exc:  # noqa: BLE001
                entry = BatchEntry(name=name, query=sql, error=str(exc))
            entries.append(entry)
            if on_entry is not None:
                on_entry(entry)

        return BatchReport(entries=entries)
