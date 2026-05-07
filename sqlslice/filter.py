"""Filter module for selecting and narrowing down ProfileResult stages."""

from typing import Callable, List, Optional
from sqlslice.profiler import ProfileResult, Stage


class FilteredResult:
    """Wraps a ProfileResult with only the stages that passed the filter."""

    def __init__(self, original: ProfileResult, stages: List[Stage]):
        self.original = original
        self.stages = stages
        self.query = original.query
        self.total_duration = sum(s.duration for s in stages)

    def summary(self) -> str:
        lines = [f"Query: {self.query}"]
        lines.append(f"Filtered stages: {len(self.stages)}")
        for stage in self.stages:
            lines.append(f"  {stage.name}: {stage.duration:.4f}s")
        lines.append(f"Filtered total: {self.total_duration:.4f}s")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"FilteredResult(query={self.query!r}, "
            f"stages={len(self.stages)}, "
            f"total={self.total_duration:.4f}s)"
        )


class ProfileFilter:
    """Applies predicates to filter stages from a ProfileResult."""

    def __init__(self):
        self._predicates: List[Callable[[Stage], bool]] = []

    def min_duration(self, threshold: float) -> "ProfileFilter":
        """Keep stages with duration >= threshold seconds."""
        if threshold < 0:
            raise ValueError("threshold must be non-negative")
        self._predicates.append(lambda s: s.duration >= threshold)
        return self

    def name_contains(self, substring: str) -> "ProfileFilter":
        """Keep stages whose name contains the given substring (case-insensitive)."""
        self._predicates.append(
            lambda s: substring.lower() in s.name.lower()
        )
        return self

    def name_in(self, names: List[str]) -> "ProfileFilter":
        """Keep stages whose name is in the provided list."""
        name_set = set(names)
        self._predicates.append(lambda s: s.name in name_set)
        return self

    def custom(self, predicate: Callable[[Stage], bool]) -> "ProfileFilter":
        """Add a custom predicate function."""
        self._predicates.append(predicate)
        return self

    def apply(self, result: ProfileResult) -> FilteredResult:
        """Apply all predicates to the result and return a FilteredResult."""
        filtered = [
            stage
            for stage in result.stages
            if all(p(stage) for p in self._predicates)
        ]
        return FilteredResult(original=result, stages=filtered)

    def reset(self) -> "ProfileFilter":
        """Clear all predicates."""
        self._predicates = []
        return self
