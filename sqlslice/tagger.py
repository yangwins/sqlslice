"""Tag-based labelling for profile results, enabling grouping and filtering by custom tags."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlslice.profiler import ProfileResult


@dataclass
class TaggedResult:
    """A ProfileResult decorated with a set of string tags."""

    result: ProfileResult
    tags: List[str] = field(default_factory=list)

    def has_tag(self, tag: str) -> bool:
        """Return True if *tag* is present (case-insensitive)."""
        return tag.lower() in (t.lower() for t in self.tags)

    def __repr__(self) -> str:  # pragma: no cover
        return f"TaggedResult(query={self.result.query!r}, tags={self.tags})"


@dataclass
class TagRegistry:
    """Stores tagged results and supports lookup by tag."""

    _records: List[TaggedResult] = field(default_factory=list, init=False, repr=False)

    def add(self, result: ProfileResult, tags: Optional[List[str]] = None) -> TaggedResult:
        """Add *result* with the supplied *tags* and return the TaggedResult."""
        if tags is None:
            tags = []
        tagged = TaggedResult(result=result, tags=[t.strip() for t in tags if t.strip()])
        self._records.append(tagged)
        return tagged

    def find_by_tag(self, tag: str) -> List[TaggedResult]:
        """Return all TaggedResults that carry *tag*."""
        return [r for r in self._records if r.has_tag(tag)]

    def all_tags(self) -> List[str]:
        """Return a sorted, deduplicated list of every tag in the registry."""
        seen: Dict[str, None] = {}
        for record in self._records:
            for t in record.tags:
                seen[t.lower()] = None
        return sorted(seen.keys())

    def count(self) -> int:
        """Return the total number of registered results."""
        return len(self._records)

    def summary(self) -> str:
        """Return a human-readable summary of the registry."""
        lines = [f"TagRegistry: {self.count()} result(s), tags: {self.all_tags()}"]
        for tr in self._records:
            lines.append(f"  [{', '.join(tr.tags) or 'untagged'}] {tr.result.query}")
        return "\n".join(lines)
