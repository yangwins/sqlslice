"""Core SQL query profiler: executes a query and captures stage-by-stage timing."""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Stage:
    """Represents a single timing stage in query execution."""
    name: str
    duration_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"Stage(name={self.name!r}, duration_ms={self.duration_ms:.3f})"


@dataclass
class ProfileResult:
    """Aggregated profiling result for a single SQL query."""
    query: str
    stages: List[Stage] = field(default_factory=list)
    total_ms: float = 0.0
    error: Optional[str] = None

    def summary(self) -> str:
        lines = [f"Query: {self.query[:80]!r}", f"Total: {self.total_ms:.3f} ms"]
        for stage in self.stages:
            pct = (stage.duration_ms / self.total_ms * 100) if self.total_ms else 0
            lines.append(f"  [{pct:5.1f}%] {stage.name}: {stage.duration_ms:.3f} ms")
        if self.error:
            lines.append(f"  ERROR: {self.error}")
        return "\n".join(lines)


class QueryProfiler:
    """Profiles SQL query execution by wrapping a DB-API 2.0 connection."""

    def __init__(self, connection: Any) -> None:
        self._conn = connection

    def profile(self, query: str, params: Optional[Any] = None) -> ProfileResult:
        """Execute *query* and return a ProfileResult with per-stage timings."""
        result = ProfileResult(query=query)
        stages: List[Stage] = []

        # Stage 1: acquire cursor
        t0 = time.perf_counter()
        try:
            cursor = self._conn.cursor()
        except Exception as exc:  # noqa: BLE001
            result.error = f"cursor acquisition failed: {exc}"
            return result
        stages.append(Stage("cursor_acquire", _elapsed_ms(t0)))

        # Stage 2: execute
        t1 = time.perf_counter()
        try:
            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
        except Exception as exc:  # noqa: BLE001
            result.error = f"execution failed: {exc}"
            result.stages = stages
            result.total_ms = sum(s.duration_ms for s in stages)
            return result
        stages.append(Stage("execute", _elapsed_ms(t1)))

        # Stage 3: fetch all rows
        t2 = time.perf_counter()
        try:
            rows = cursor.fetchall()
        except Exception as exc:  # noqa: BLE001
            result.error = f"fetch failed: {exc}"
            result.stages = stages
            result.total_ms = sum(s.duration_ms for s in stages)
            return result
        fetch_stage = Stage("fetchall", _elapsed_ms(t2), {"row_count": len(rows)})
        stages.append(fetch_stage)

        result.stages = stages
        result.total_ms = sum(s.duration_ms for s in stages)
        return result


def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000
