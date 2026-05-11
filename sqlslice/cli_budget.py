"""CLI entry-point for budget-based stage timing checks."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List, Optional

from sqlslice.budget import QueryBudget
from sqlslice.profiler import QueryProfiler


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqlslice-budget",
        description="Run a query and check each stage against time budgets.",
    )
    p.add_argument("dsn", help="Database connection string.")
    p.add_argument("query", help="SQL query to profile.")
    p.add_argument(
        "--budget",
        metavar="STAGE=MS",
        action="append",
        default=[],
        help="Per-stage budget in ms, e.g. --budget execute=200. Repeatable.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit results as JSON.",
    )
    p.add_argument(
        "--fail-on-violation",
        action="store_true",
        help="Exit with code 1 if any budget is exceeded.",
    )
    return p


def _parse_budgets(raw: List[str]) -> Dict[str, float]:
    budgets: Dict[str, float] = {}
    for item in raw:
        if "=" not in item:
            raise SystemExit(f"Invalid budget spec {item!r}. Expected STAGE=MS.")
        stage, ms_str = item.split("=", 1)
        try:
            budgets[stage.strip()] = float(ms_str.strip())
        except ValueError:
            raise SystemExit(f"Budget value for {stage!r} is not a number: {ms_str!r}")
    return budgets


def run_budget_session(
    dsn: str,
    query: str,
    budgets: Dict[str, float],
    as_json: bool = False,
    fail_on_violation: bool = False,
    out=None,
) -> int:
    if out is None:
        out = sys.stdout

    profiler = QueryProfiler(dsn)
    result = profiler.profile(query)
    checker = QueryBudget(budgets)
    report = checker.check(result)

    if as_json:
        payload = {
            "query": report.query,
            "has_violations": report.has_violations,
            "total_excess_ms": report.total_excess_ms,
            "violations": [
                {
                    "stage": v.stage_name,
                    "budget_ms": v.budget_ms,
                    "actual_ms": v.actual_ms,
                    "excess_ms": v.excess_ms,
                }
                for v in report.violations
            ],
            "unchecked_stages": report.unchecked_stages,
        }
        out.write(json.dumps(payload, indent=2) + "\n")
    else:
        out.write(report.summary() + "\n")

    return 1 if (fail_on_violation and report.has_violations) else 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    budgets = _parse_budgets(args.budget)
    if not budgets:
        parser.error("Provide at least one --budget STAGE=MS argument.")
    code = run_budget_session(
        dsn=args.dsn,
        query=args.query,
        budgets=budgets,
        as_json=args.as_json,
        fail_on_violation=args.fail_on_violation,
    )
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
