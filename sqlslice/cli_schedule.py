"""CLI entry point for running sqlslice in scheduled/watch mode.

Usage example (programmatic):
    from sqlslice.cli_schedule import run_scheduled_session
    run_scheduled_session(profiler, interval=30, max_runs=10)
"""

from __future__ import annotations

import signal
import sys
import time
from typing import Optional

from sqlslice.profiler import QueryProfiler
from sqlslice.scheduler import QueryScheduler, ScheduleReport, ScheduledRun


def _default_on_result(run: ScheduledRun) -> None:
    status = "OK" if run.result.error is None else f"ERROR: {run.result.error}"
    ts = time.strftime("%H:%M:%S", time.localtime(run.timestamp))
    duration = (
        f"{run.result.total_duration:.4f}s"
        if run.result.error is None
        else "N/A"
    )
    print(f"[{ts}] Run #{run.run_index:>3}  duration={duration}  status={status}")


def run_scheduled_session(
    profiler: QueryProfiler,
    interval: float = 60.0,
    max_runs: Optional[int] = None,
    verbose: bool = True,
) -> ScheduleReport:
    """Block until *max_runs* have completed (or SIGINT), then return a ScheduleReport.

    Args:
        profiler:  A configured :class:`QueryProfiler` instance.
        interval:  Seconds between consecutive runs.
        max_runs:  Stop automatically after this many runs.  ``None`` means run
                   until interrupted.
        verbose:   Print a one-liner after each run when *True*.

    Returns:
        A :class:`ScheduleReport` summarising all collected runs.
    """
    callback = _default_on_result if verbose else None
    scheduler = QueryScheduler(
        profiler=profiler,
        interval=interval,
        max_runs=max_runs,
        on_result=callback,
    )

    report: Optional[ScheduleReport] = None

    def _handle_sigint(sig, frame):  # noqa: ANN001
        nonlocal report
        print("\nInterrupted — stopping scheduler…", file=sys.stderr)
        report = scheduler.stop()
        sys.exit(0)

    original_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, _handle_sigint)

    try:
        scheduler.start()
        # Wait for the background thread to finish (max_runs reached)
        if scheduler._thread:
            scheduler._thread.join()
        report = scheduler.stop()
    finally:
        signal.signal(signal.SIGINT, original_handler)

    if verbose and report:
        print("\n" + "=" * 60)
        print(report.summary())

    return report  # type: ignore[return-value]
