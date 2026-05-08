"""Scheduled profiling: run a query profiler on a recurring interval and collect results."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from sqlslice.profiler import ProfileResult, QueryProfiler


@dataclass
class ScheduledRun:
    """Record of a single scheduled profiler execution."""
    run_index: int
    timestamp: float
    result: ProfileResult

    def __repr__(self) -> str:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.timestamp))
        status = "ok" if self.result.error is None else "error"
        return f"<ScheduledRun #{self.run_index} at={ts} status={status}>"


@dataclass
class ScheduleReport:
    """Aggregated report produced after a scheduled session ends."""
    query: str
    runs: List[ScheduledRun] = field(default_factory=list)

    @property
    def run_count(self) -> int:
        return len(self.runs)

    @property
    def successful_runs(self) -> List[ScheduledRun]:
        return [r for r in self.runs if r.result.error is None]

    @property
    def failed_runs(self) -> List[ScheduledRun]:
        return [r for r in self.runs if r.result.error is not None]

    def summary(self) -> str:
        lines = [
            f"Query     : {self.query}",
            f"Total runs: {self.run_count}",
            f"Successful: {len(self.successful_runs)}",
            f"Failed    : {len(self.failed_runs)}",
        ]
        if self.successful_runs:
            durations = [r.result.total_duration for r in self.successful_runs]
            lines.append(f"Avg duration (s): {sum(durations)/len(durations):.4f}")
            lines.append(f"Min duration (s): {min(durations):.4f}")
            lines.append(f"Max duration (s): {max(durations):.4f}")
        return "\n".join(lines)


class QueryScheduler:
    """Runs a QueryProfiler repeatedly at a fixed interval."""

    def __init__(
        self,
        profiler: QueryProfiler,
        interval: float = 60.0,
        max_runs: Optional[int] = None,
        on_result: Optional[Callable[[ScheduledRun], None]] = None,
    ) -> None:
        if interval <= 0:
            raise ValueError("interval must be positive")
        self._profiler = profiler
        self._interval = interval
        self._max_runs = max_runs
        self._on_result = on_result
        self._runs: List[ScheduledRun] = []
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _execute_once(self, index: int) -> ScheduledRun:
        result = self._profiler.run()
        run = ScheduledRun(run_index=index, timestamp=time.time(), result=result)
        self._runs.append(run)
        if self._on_result:
            self._on_result(run)
        return run

    def _loop(self) -> None:
        index = 0
        while not self._stop_event.is_set():
            if self._max_runs is not None and index >= self._max_runs:
                break
            self._execute_once(index)
            index += 1
            self._stop_event.wait(timeout=self._interval)

    def start(self) -> None:
        """Start the scheduler in a background thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> ScheduleReport:
        """Stop the scheduler and return a ScheduleReport."""
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        return ScheduleReport(query=self._profiler.query, runs=list(self._runs))

    def run_once(self) -> ScheduledRun:
        """Execute a single profiling run synchronously."""
        index = len(self._runs)
        return self._execute_once(index)
