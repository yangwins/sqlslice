"""Query truncator: shortens long SQL strings for display while preserving key structure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


_DEFAULT_MAX_LENGTH = 120
_ELLIPSIS = "..."


@dataclass
class TruncatedQuery:
    original: str
    truncated: str
    was_truncated: bool
    original_length: int
    truncated_length: int

    def __repr__(self) -> str:
        flag = "*" if self.was_truncated else ""
        return f"TruncatedQuery({self.truncated_length}/{self.original_length} chars{flag})"


class QueryTruncator:
    """Truncates SQL query strings to a maximum display length."""

    def __init__(self, max_length: int = _DEFAULT_MAX_LENGTH) -> None:
        if not isinstance(max_length, int) or max_length <= 0:
            raise ValueError(f"max_length must be a positive integer, got {max_length!r}")
        if max_length <= len(_ELLIPSIS):
            raise ValueError(
                f"max_length must be greater than {len(_ELLIPSIS)} (ellipsis length)"
            )
        self.max_length = max_length

    def truncate(self, query: str, *, placeholder: Optional[str] = None) -> TruncatedQuery:
        """Truncate *query* to at most *max_length* characters.

        Args:
            query: Raw SQL string to truncate.
            placeholder: Override the trailing ellipsis with a custom string.

        Returns:
            A :class:`TruncatedQuery` describing the result.
        """
        if not isinstance(query, str):
            raise TypeError(f"query must be a str, got {type(query).__name__!r}")

        suffix = placeholder if placeholder is not None else _ELLIPSIS
        original_length = len(query)

        if original_length <= self.max_length:
            return TruncatedQuery(
                original=query,
                truncated=query,
                was_truncated=False,
                original_length=original_length,
                truncated_length=original_length,
            )

        cut = self.max_length - len(suffix)
        truncated = query[:cut].rstrip() + suffix
        return TruncatedQuery(
            original=query,
            truncated=truncated,
            was_truncated=True,
            original_length=original_length,
            truncated_length=len(truncated),
        )

    def truncate_many(self, queries: list[str]) -> list[TruncatedQuery]:
        """Truncate a list of query strings."""
        return [self.truncate(q) for q in queries]
