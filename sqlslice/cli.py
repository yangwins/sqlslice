"""Main CLI entry point for sqlslice.

Provides a unified command-line interface that ties together
the profiler, formatter, analyzer, comparator, and export utilities.
"""

import argparse
import sys
import sqlite3
from typing import Optional

from sqlslice.profiler import QueryProfiler
from sqlslice.formatter import get_formatter
from sqlslice.analyzer import QueryAnalyzer
from sqlslice.export import to_json, to_csv, save
from sqlslice.reporter import Reporter


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="sqlslice",
        description="Lightweight SQL query profiler with stage-by-stage timing reports.",
    )
    parser.add_argument(
        "--version", action="version", version="sqlslice 0.1.0"
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # --- profile subcommand ---
    profile_parser = subparsers.add_parser(
        "profile",
        help="Profile a SQL query against a SQLite database.",
    )
    profile_parser.add_argument("db", help="Path to the SQLite database file.")
    profile_parser.add_argument("query", help="SQL query to profile.")
    profile_parser.add_argument(
        "--name", default="query", help="Friendly name for the query (default: 'query')."
    )
    profile_parser.add_argument(
        "--format",
        choices=["text", "html"],
        default="text",
        help="Output format (default: text).",
    )
    profile_parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run the analyzer and show bottleneck report.",
    )
    profile_parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Bottleneck threshold fraction for --analyze (default: 0.3).",
    )
    profile_parser.add_argument(
        "--export-json",
        metavar="FILE",
        help="Export profiling result to a JSON file.",
    )
    profile_parser.add_argument(
        "--export-csv",
        metavar="FILE",
        help="Export profiling result to a CSV file.",
    )

    return parser


def _run_profile(args: argparse.Namespace) -> int:
    """Execute the 'profile' subcommand. Returns an exit code."""
    try:
        conn = sqlite3.connect(args.db)
    except Exception as exc:  # pragma: no cover
        print(f"[sqlslice] Error connecting to database: {exc}", file=sys.stderr)
        return 1

    profiler = QueryProfiler(conn)
    result = profiler.profile(args.query, name=args.name)

    formatter = get_formatter(args.format)
    print(formatter.format(result))

    if args.analyze:
        analyzer = QueryAnalyzer(threshold=args.threshold)
        report = analyzer.analyze(result)
        print()
        print(report.summary())

    if args.export_json:
        try:
            save(to_json(result), args.export_json)
            print(f"[sqlslice] JSON exported to {args.export_json}")
        except OSError as exc:
            print(f"[sqlslice] Failed to write JSON: {exc}", file=sys.stderr)
            return 1

    if args.export_csv:
        try:
            save(to_csv(result), args.export_csv)
            print(f"[sqlslice] CSV exported to {args.export_csv}")
        except OSError as exc:
            print(f"[sqlslice] Failed to write CSV: {exc}", file=sys.stderr)
            return 1

    conn.close()
    return 0


def main(argv: Optional[list] = None) -> int:
    """Entry point for the sqlslice CLI.

    Args:
        argv: Argument list (defaults to sys.argv if None).

    Returns:
        Integer exit code.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "profile":
        return _run_profile(args)

    # No subcommand given — print help.
    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
