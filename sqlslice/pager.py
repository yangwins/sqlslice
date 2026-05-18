"""Pager: splits a list of stages into pages for paginated output."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class PageResult:
    query: str
    page: int
    page_size: int
    total_stages: int
    stages: List[Stage] = field(default_factory=list)

    @property
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 0
        return max(1, (self.total_stages + self.page_size - 1) // self.page_size)

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    def summary(self) -> str:
        lines = [
            f"Query : {self.query}",
            f"Page  : {self.page} / {self.total_pages}  "
            f"(page_size={self.page_size}, total_stages={self.total_stages})",
        ]
        for s in self.stages:
            lines.append(f"  {s.name}: {s.duration_ms:.3f} ms")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"PageResult(query={self.query!r}, page={self.page}, "
            f"total_pages={self.total_pages}, stages={len(self.stages)})"
        )


class StagePager:
    """Paginates stages from a ProfileResult."""

    def __init__(self, page_size: int = 5) -> None:
        if not isinstance(page_size, int) or page_size <= 0:
            raise ValueError("page_size must be a positive integer")
        self.page_size = page_size

    def get_page(self, result: ProfileResult, page: int = 1) -> PageResult:
        """Return a PageResult for the requested 1-based page number."""
        if not isinstance(page, int) or page < 1:
            raise ValueError("page must be a positive integer")

        stages = result.stages
        total = len(stages)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)

        if page > total_pages:
            raise ValueError(
                f"page {page} out of range (total_pages={total_pages})"
            )

        start = (page - 1) * self.page_size
        end = start + self.page_size
        sliced = stages[start:end]

        return PageResult(
            query=result.query,
            page=page,
            page_size=self.page_size,
            total_stages=total,
            stages=sliced,
        )

    def all_pages(self, result: ProfileResult) -> List[PageResult]:
        """Return all pages for the given result."""
        stages = result.stages
        total = len(stages)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        return [self.get_page(result, p) for p in range(1, total_pages + 1)]
