"""Normalizes SQL query strings for consistent comparison and display."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class NormalizedQuery:
    original: str
    normalized: str
    tokens: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"NormalizedQuery(tokens={len(self.tokens)})"

    def fingerprint(self) -> str:
        """Return a compact fingerprint string for grouping similar queries."""
        return re.sub(r'\s+', ' ', self.normalized).strip().lower()


class QueryNormalizer:
    """Strips literals, normalises whitespace, and upper-cases keywords."""

    # SQL keywords to upper-case
    _KEYWORDS = {
        'select', 'from', 'where', 'join', 'left', 'right', 'inner',
        'outer', 'on', 'and', 'or', 'not', 'in', 'is', 'null', 'as',
        'order', 'by', 'group', 'having', 'limit', 'offset', 'union',
        'insert', 'into', 'update', 'set', 'delete', 'with', 'distinct',
    }

    def normalize(self, query: str) -> NormalizedQuery:
        """Return a NormalizedQuery for *query*."""
        if not isinstance(query, str):
            raise TypeError(f"query must be a str, got {type(query).__name__}")
        q = query.strip()
        if not q:
            raise ValueError("query must not be empty")

        # Replace string literals
        q = re.sub(r"'[^']*'", "'?'", q)
        # Replace numeric literals
        q = re.sub(r'\b\d+(\.\d+)?\b', '?', q)
        # Collapse whitespace
        q = re.sub(r'\s+', ' ', q)

        tokens = q.split()
        upper_tokens = [
            t.upper() if t.lower() in self._KEYWORDS else t
            for t in tokens
        ]
        normalized = ' '.join(upper_tokens)
        return NormalizedQuery(
            original=query.strip(),
            normalized=normalized,
            tokens=upper_tokens,
        )

    def are_equivalent(self, query_a: str, query_b: str) -> bool:
        """Return True if two queries share the same fingerprint."""
        a = self.normalize(query_a).fingerprint()
        b = self.normalize(query_b).fingerprint()
        return a == b
