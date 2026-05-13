"""Export utilities for OutlierReport."""
from __future__ import annotations

import csv
import io
import json
from typing import IO

from sqlslice.outlier import OutlierReport


def outlier_to_json(report: OutlierReport) -> str:
    """Serialise an OutlierReport to a JSON string."""
    data = {
        "query": report.query,
        "mean_ms": report.mean_ms,
        "stdev_ms": report.stdev_ms,
        "threshold": report.threshold,
        "has_outliers": report.has_outliers,
        "outliers": [
            {
                "stage": o.stage.name,
                "duration_ms": o.stage.duration_ms,
                "z_score": o.z_score,
                "deviation_ms": o.deviation_ms,
            }
            for o in report.outliers
        ],
    }
    return json.dumps(data, indent=2)


def outlier_to_csv(report: OutlierReport) -> str:
    """Serialise an OutlierReport to CSV text."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["stage", "duration_ms", "z_score", "deviation_ms"])
    for o in report.outliers:
        writer.writerow(
            [o.stage.name, f"{o.stage.duration_ms:.4f}", f"{o.z_score:.4f}", f"{o.deviation_ms:.4f}"]
        )
    return buf.getvalue()


def write_outlier_to_stream(report: OutlierReport, stream: IO[str], fmt: str = "json") -> None:
    """Write report to an open text stream in *fmt* format ('json' or 'csv')."""
    if fmt == "csv":
        stream.write(outlier_to_csv(report))
    else:
        stream.write(outlier_to_json(report))


def save_outlier(report: OutlierReport, path: str, fmt: str = "json") -> None:
    """Save report to *path* in *fmt* format."""
    with open(path, "w", encoding="utf-8") as fh:
        write_outlier_to_stream(report, fh, fmt)
