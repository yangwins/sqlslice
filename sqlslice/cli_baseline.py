"""CLI entry point for baseline management (save, load, list, delete)."""

from __future__ import annotations

import argparse
import sys

from sqlslice.baseline import BaselineStore
from sqlslice.profiler import ProfileResult, Stage


DEFAULT_STORE = "baselines.json"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlslice-baseline",
        description="Manage sqlslice query baselines.",
    )
    parser.add_argument(
        "--store",
        default=DEFAULT_STORE,
        metavar="FILE",
        help="Path to baseline JSON store (default: baselines.json)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    lst = sub.add_parser("list", help="List all saved baseline names.")
    lst  # noqa: used for side-effect

    show = sub.add_parser("show", help="Show details of a baseline.")
    show.add_argument("name", help="Baseline name to show.")

    delete = sub.add_parser("delete", help="Delete a saved baseline.")
    delete.add_argument("name", help="Baseline name to delete.")

    return parser


def _cmd_list(store: BaselineStore) -> None:
    names = store.list_names()
    if not names:
        print("No baselines saved.")
        return
    print(f"Saved baselines ({len(names)}):")
    for name in names:
        record = store.load(name)
        print(f"  {name}  —  total={record.total_duration:.4f}s  stages={len(record.stages)}")


def _cmd_show(store: BaselineStore, name: str) -> None:
    record = store.load(name)
    if record is None:
        print(f"Baseline {name!r} not found.", file=sys.stderr)
        sys.exit(1)
    print(f"Baseline : {record.name}")
    print(f"Query    : {record.query}")
    print(f"Total    : {record.total_duration:.4f}s")
    print("Stages:")
    for s in record.stages:
        err = f"  [error: {s.error}]" if s.error else ""
        print(f"  {s.name:<20} {s.duration:.4f}s{err}")


def _cmd_delete(store: BaselineStore, name: str) -> None:
    removed = store.delete(name)
    if removed:
        print(f"Deleted baseline {name!r}.")
    else:
        print(f"Baseline {name!r} not found.", file=sys.stderr)
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    store = BaselineStore(path=args.store)

    if args.command == "list":
        _cmd_list(store)
    elif args.command == "show":
        _cmd_show(store, args.name)
    elif args.command == "delete":
        _cmd_delete(store, args.name)


if __name__ == "__main__":  # pragma: no cover
    main()
