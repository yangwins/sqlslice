"""CLI entry-point: profile a query and print a stage ranking report."""
from __future__ import annotations

import argparse
import sqlite3
import sys

from sqlslice.profiler import QueryProfiler
from sqlslice.ranker import StageRanker


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlslice-rank",
        description="Profile a SQL query and rank its stages by duration.",
    )
    parser.add_argument("db", help="Path to the SQLite database file.")
    parser.add_argument("query", help="SQL query to profile and rank.")
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        metavar="N",
        help="Number of profiling runs to average over (default: 1).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="K",
        help="Show only the top K slowest stages.",
    )
    return parser


def run_rank_session(
    db_path: str,
    query: str,
    runs: int = 1,
    top: int | None = None,
    out=None,
) -> int:
    """Run ranking session; returns exit code (0 = success, 1 = error)."""
    if out is None:
        out = sys.stdout

    if runs < 1:
        print("error: --runs must be >= 1", file=sys.stderr)
        return 1

    try:
        conn = sqlite3.connect(db_path)
    except Exception as exc:  # pragma: no cover
        print(f"error: cannot open database: {exc}", file=sys.stderr)
        return 1

    ranker = StageRanker()
    profiler = QueryProfiler(conn)
    exit_code = 0

    for run_idx in range(1, runs + 1):
        result = profiler.profile(query)
        report = ranker.rank(result)

        if runs > 1:
            print(f"--- Run {run_idx}/{runs} ---", file=out)

        if top is not None:
            ranked = report.ranked_stages[:top]
            from sqlslice.ranker import RankReport
            report = RankReport(query=report.query, ranked_stages=ranked)

        print(report.summary(), file=out)

        if any(s.stage.error for s in report.ranked_stages):
            exit_code = 1

    conn.close()
    return exit_code


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    code = run_rank_session(
        db_path=args.db,
        query=args.query,
        runs=args.runs,
        top=args.top,
    )
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
