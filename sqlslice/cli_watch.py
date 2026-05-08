"""CLI entry point for the sqlslice watchdog: run a query N times and report threshold violations."""

import argparse
import sys
from typing import List

from sqlslice.profiler import QueryProfiler, ProfileResult
from sqlslice.watchdog import QueryWatchdog, WatchdogAlert


def _print_alert(alert: WatchdogAlert) -> None:
    print(f"  [ALERT] run #{alert.run_index}: {alert.total_duration:.4f}s > {alert.threshold:.4f}s", flush=True)


def run_watch_session(
    query: str,
    profiler: QueryProfiler,
    runs: int,
    threshold: float,
    verbose: bool = False,
) -> int:
    """Run the watchdog session. Returns exit code (0 = no alerts, 1 = alerts found)."""
    results: List[ProfileResult] = []

    print(f"sqlslice watchdog | query: {query!r} | runs: {runs} | threshold: {threshold}s")

    for i in range(runs):
        result = profiler.run(query)
        results.append(result)
        if verbose:
            total = sum(s.duration for s in result.stages)
            status = "ERROR" if result.error else f"{total:.4f}s"
            print(f"  run {i:>3}: {status}")

    on_alert = _print_alert if verbose else None
    watchdog = QueryWatchdog(threshold=threshold, on_alert=on_alert)
    report = watchdog.watch(results)

    print()
    print(report.summary())

    return 1 if report.alert_count > 0 else 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlslice-watch",
        description="Run a SQL query repeatedly and alert when duration exceeds a threshold.",
    )
    parser.add_argument("query", help="SQL query to profile")
    parser.add_argument("--runs", type=int, default=5, help="Number of times to run the query (default: 5)")
    parser.add_argument("--threshold", type=float, default=1.0, help="Alert threshold in seconds (default: 1.0)")
    parser.add_argument("--dsn", default="sqlite:///:memory:", help="Database DSN (default: sqlite:///:memory:)")
    parser.add_argument("--verbose", action="store_true", help="Print per-run timings")
    return parser


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    import sqlalchemy
    engine = sqlalchemy.create_engine(args.dsn)
    profiler = QueryProfiler(engine)

    exit_code = run_watch_session(
        query=args.query,
        profiler=profiler,
        runs=args.runs,
        threshold=args.threshold,
        verbose=args.verbose,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
