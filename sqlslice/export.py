"""Export helpers: write ProfileResult reports to files or streams."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from sqlslice.profiler import ProfileResult


def to_json(result: "ProfileResult", indent: int = 2) -> str:
    """Serialise a ProfileResult to a JSON string."""
    total = result.total_duration
    payload = {
        "query": result.query,
        "total_duration": total,
        "stages": [
            {
                "name": s.name,
                "duration": s.duration,
                "share": round(s.duration / total * 100, 2) if total else 0.0,
                "error": s.error,
            }
            for s in result.stages
        ],
    }
    return json.dumps(payload, indent=indent)


def to_csv(result: "ProfileResult") -> str:
    """Serialise a ProfileResult to a CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["stage", "duration_s", "share_pct", "error"])
    total = result.total_duration
    for s in result.stages:
        share = round(s.duration / total * 100, 2) if total else 0.0
        writer.writerow([s.name, s.duration, share, s.error or ""])
    return buf.getvalue()


def save(result: "ProfileResult", path: str | Path, fmt: str = "json") -> Path:
    """Write a ProfileResult to *path* in the given format ('json' or 'csv').

    Returns the resolved Path that was written.
    """
    path = Path(path)
    if fmt == "json":
        content = to_json(result)
    elif fmt == "csv":
        content = to_csv(result)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Use 'json' or 'csv'.")
    path.write_text(content, encoding="utf-8")
    return path


def write_to_stream(result: "ProfileResult", stream: TextIO, fmt: str = "json") -> None:
    """Write a ProfileResult to an open text stream."""
    if fmt == "json":
        stream.write(to_json(result))
    elif fmt == "csv":
        stream.write(to_csv(result))
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Use 'json' or 'csv'.")
