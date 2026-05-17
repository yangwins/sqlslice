"""Export utilities for GroupReport — JSON and CSV serialisation."""
from __future__ import annotations

import csv
import io
import json
import os
from typing import IO

from sqlslice.grouper import GroupReport


def group_to_json(report: GroupReport, indent: int = 2) -> str:
    """Serialise a GroupReport to a JSON string."""
    payload = {
        "query": report.query,
        "bucket_count": report.bucket_count,
        "buckets": [
            {
                "key": b.key,
                "count": b.count,
                "total_duration_ms": round(b.total_duration_ms, 4),
                "avg_duration_ms": round(b.avg_duration_ms, 4),
            }
            for b in report.buckets
        ],
    }
    return json.dumps(payload, indent=indent)


def group_to_csv(report: GroupReport) -> str:
    """Serialise a GroupReport to a CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["key", "count", "total_duration_ms", "avg_duration_ms"])
    for b in report.buckets:
        writer.writerow(
            [
                b.key,
                b.count,
                round(b.total_duration_ms, 4),
                round(b.avg_duration_ms, 4),
            ]
        )
    return buf.getvalue()


def write_group_to_stream(report: GroupReport, stream: IO[str], fmt: str = "json") -> None:
    """Write a GroupReport to an open text stream.

    Parameters
    ----------
    report:
        The GroupReport to serialise.
    stream:
        An open, writable text stream.
    fmt:
        ``"json"`` (default) or ``"csv"``.
    """
    if fmt == "csv":
        stream.write(group_to_csv(report))
    else:
        stream.write(group_to_json(report))


def save_group(report: GroupReport, path: str, fmt: str = "json") -> None:
    """Persist a GroupReport to *path*.

    The parent directory is created if it does not exist.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        write_group_to_stream(report, fh, fmt=fmt)
