"""Export helpers for RegressionReport."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import IO

from sqlslice.regression import RegressionReport


def regression_to_json(report: RegressionReport) -> str:
    """Serialise a RegressionReport to a JSON string."""
    payload = {
        "query": report.query,
        "threshold_pct": report.threshold_pct,
        "has_regressions": report.has_regressions,
        "flags": [
            {
                "stage": f.stage_name,
                "baseline_ms": f.baseline_ms,
                "current_ms": f.current_ms,
                "delta_ms": f.delta_ms,
                "pct_change": f.pct_change,
            }
            for f in report.flags
        ],
    }
    return json.dumps(payload, indent=2)


def regression_to_csv(report: RegressionReport) -> str:
    """Serialise a RegressionReport to a CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["stage", "baseline_ms", "current_ms", "delta_ms", "pct_change"])
    for f in report.flags:
        writer.writerow(
            [f.stage_name, f.baseline_ms, f.current_ms, f.delta_ms, f.pct_change]
        )
    return buf.getvalue()


def write_regression_to_stream(report: RegressionReport, stream: IO[str], fmt: str = "json") -> None:
    """Write a RegressionReport to an open text stream."""
    if fmt == "csv":
        stream.write(regression_to_csv(report))
    else:
        stream.write(regression_to_json(report))


def save_regression(report: RegressionReport, path: str | Path, fmt: str = "json") -> None:
    """Persist a RegressionReport to *path* in the requested format."""
    with open(path, "w", encoding="utf-8") as fh:
        write_regression_to_stream(report, fh, fmt=fmt)
