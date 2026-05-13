"""Tests for sqlslice.export_outlier."""
import csv
import io
import json
import os
import tempfile

import pytest

from sqlslice.export_outlier import (
    outlier_to_csv,
    outlier_to_json,
    save_outlier,
    write_outlier_to_stream,
)
from sqlslice.outlier import OutlierDetector
from sqlslice.profiler import ProfileResult, Stage


@pytest.fixture()
def report():
    stages = [
        Stage(name="parse", duration_ms=10.0),
        Stage(name="plan", duration_ms=11.0),
        Stage(name="execute", duration_ms=300.0),
        Stage(name="fetch", duration_ms=9.0),
    ]
    result = ProfileResult(query="SELECT *", stages=stages, total_duration_ms=330.0)
    return OutlierDetector(threshold=1.5).detect(result)


def test_to_json_is_valid(report):
    raw = outlier_to_json(report)
    data = json.loads(raw)
    assert isinstance(data, dict)


def test_to_json_has_query(report):
    data = json.loads(outlier_to_json(report))
    assert data["query"] == "SELECT *"


def test_to_json_has_outliers_list(report):
    data = json.loads(outlier_to_json(report))
    assert "outliers" in data
    assert isinstance(data["outliers"], list)


def test_to_json_outlier_fields(report):
    data = json.loads(outlier_to_json(report))
    assert report.has_outliers
    first = data["outliers"][0]
    assert "stage" in first
    assert "duration_ms" in first
    assert "z_score" in first
    assert "deviation_ms" in first


def test_to_csv_has_header(report):
    raw = outlier_to_csv(report)
    reader = csv.reader(io.StringIO(raw))
    header = next(reader)
    assert "stage" in header
    assert "z_score" in header


def test_to_csv_row_per_outlier(report):
    raw = outlier_to_csv(report)
    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)
    # header + one row per outlier
    assert len(rows) == 1 + len(report.outliers)


def test_write_to_stream_json(report):
    buf = io.StringIO()
    write_outlier_to_stream(report, buf, fmt="json")
    data = json.loads(buf.getvalue())
    assert data["query"] == "SELECT *"


def test_write_to_stream_csv(report):
    buf = io.StringIO()
    write_outlier_to_stream(report, buf, fmt="csv")
    assert "stage" in buf.getvalue()


def test_save_outlier_json(report):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "out.json")
        save_outlier(report, path, fmt="json")
        with open(path) as f:
            data = json.load(f)
        assert data["query"] == "SELECT *"


def test_save_outlier_csv(report):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "out.csv")
        save_outlier(report, path, fmt="csv")
        with open(path) as f:
            content = f.read()
        assert "stage" in content
