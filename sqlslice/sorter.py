"""Stage sorter — reorders profiled stages by a chosen criterion."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

from sqlslice.profiler import ProfileResult, Stage

SortKey = Literal["duration", "name", "index"]
SortOrder = Literal["asc", "desc"]


@dataclass
class SortReport:
    query: str
    key: SortKey
    order: SortOrder
    stages: List[Stage]

    def summary(self) -> str:
        lines = [
            f"Query : {self.query}",
            f"Sorted: {self.key} ({self.order})",
            "",
        ]
        for i, s in enumerate(self.stages, 1):
            lines.append(f"  {i:>2}. {s.name:<30} {s.duration_ms:.2f} ms")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"SortReport(key={self.key!r}, order={self.order!r}, "
            f"stages={len(self.stages)})"
        )


class StageSorter:
    """Sort the stages of a :class:`ProfileResult` by a given key."""

    VALID_KEYS: tuple = ("duration", "name", "index")
    VALID_ORDERS: tuple = ("asc", "desc")

    def __init__(
        self,
        key: SortKey = "duration",
        order: SortOrder = "desc",
    ) -> None:
        if key not in self.VALID_KEYS:
            raise ValueError(
                f"Invalid sort key {key!r}. Choose from {self.VALID_KEYS}."
            )
        if order not in self.VALID_ORDERS:
            raise ValueError(
                f"Invalid order {order!r}. Choose from {self.VALID_ORDERS}."
            )
        self.key = key
        self.order = order

    # ------------------------------------------------------------------
    def sort(self, result: ProfileResult) -> SortReport:
        """Return a :class:`SortReport` with stages reordered."""
        reverse = self.order == "desc"

        if self.key == "duration":
            keyfn = lambda s: s.duration_ms  # noqa: E731
        elif self.key == "name":
            keyfn = lambda s: s.name.lower()  # noqa: E731
        else:  # index — restore original order
            keyfn = lambda s: result.stages.index(s)  # noqa: E731

        sorted_stages = sorted(result.stages, key=keyfn, reverse=reverse)

        return SortReport(
            query=result.query,
            key=self.key,
            order=self.order,
            stages=sorted_stages,
        )
