"""Stage-level query splitter: breaks a ProfileResult into sub-results by stage predicate."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class SplitSlice:
    """A named subset of stages extracted from a ProfileResult."""

    name: str
    query: str
    stages: List[Stage]
    total_duration_ms: float = field(init=False)

    def __post_init__(self) -> None:
        self.total_duration_ms = sum(s.duration_ms for s in self.stages)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SplitSlice(name={self.name!r}, stages={len(self.stages)}, "
            f"total_ms={self.total_duration_ms:.3f})"
        )


@dataclass
class SplitReport:
    """Container for all slices produced by a QuerySplitter run."""

    query: str
    slices: List[SplitSlice]

    @property
    def slice_count(self) -> int:
        return len(self.slices)

    def get(self, name: str) -> Optional[SplitSlice]:
        """Return the first slice with the given name, or None."""
        for s in self.slices:
            if s.name == name:
                return s
        return None

    def summary(self) -> str:
        lines = [f"SplitReport for: {self.query}", f"  Slices: {self.slice_count}"]
        for sl in self.slices:
            lines.append(f"  [{sl.name}] {len(sl.stages)} stage(s), {sl.total_duration_ms:.3f} ms")
        return "\n".join(lines)

    def __repr__(self) -> str:  # pragma: no cover
        return f"SplitReport(query={self.query!r}, slices={self.slice_count})"


class QuerySplitter:
    """Splits a ProfileResult into named slices based on user-supplied predicates."""

    def __init__(self) -> None:
        self._predicates: List[tuple[str, Callable[[Stage], bool]]] = []

    def add_slice(self, name: str, predicate: Callable[[Stage], bool]) -> "QuerySplitter":
        """Register a named predicate.  Returns self for chaining."""
        if not name or not name.strip():
            raise ValueError("Slice name must be a non-empty string.")
        self._predicates.append((name, predicate))
        return self

    def split(self, result: ProfileResult) -> SplitReport:
        """Apply all registered predicates and return a SplitReport."""
        if not self._predicates:
            raise ValueError("No slice predicates registered; call add_slice() first.")

        slices: List[SplitSlice] = []
        for name, pred in self._predicates:
            matched = [s for s in result.stages if pred(s)]
            slices.append(SplitSlice(name=name, query=result.query, stages=matched))

        return SplitReport(query=result.query, slices=slices)
