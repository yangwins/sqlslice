"""Tests for sqlslice.export_regression."""
import csv
import io
import json
import tempfile
from pathlib import Path

import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.regression import RegressionDetector, RegressionReport
from sqlslice.export_regression import (
    regression_to_csv,
    regression_to_json,
    save_regression,
    write_regression_to_stream,
)

QUERY = "SELECT 1"


@pytest.fixture
def report():
    detector = RegressionDetector(threshold_pct=10.0)
    base = ProfileResult(query=QUERY, stages=[Stage("parse", 10.0), Stage("execute", 100.0)])
    cur = ProfileResult(query=QUERY, stages=[Stage("parse", 10.5), Stage("execute", 160.0)])
    return detector.detect(base, cur)


def test_to_json_is_valid(report):
    data = json.loads(regression_to_json(report))
    assert isinstance(data, dict)


def test_to_json_has_query(report):
    data = json.loads(regression_to_json(report))
    assert data["query"] == QUERY


def test_to_json_has_flags_list(report):
    data = json.loads(regression_to_json(report))
    assert isinstance(data["flags"], list)


def test_to_json_flag_fields(report):
    data = json.loads(regression_to_json(report))
    flag = data["flags"][0]
    assert "stage" in flag
    assert "baseline_ms" in flag
    assert "current_ms" in flag
    assert "delta_ms" in flag
    assert "pct_change" in flag


def test_to_json_has_regressions_true(report):
    data = json.loads(regression_to_json(report))
    assert data["has_regressions"] is True


def test_to_csv_is_string(report):
    result = regression_to_csv(report)
    assert isinstance(result, str)


def test_to_csv_has_header(report):
    result = regression_to_csv(report)
    reader = csv.reader(io.StringIO(result))
    header = next(reader)
    assert "stage" in header
    assert "delta_ms" in header


def test_to_csv_row_count(report):
    result = regression_to_csv(report)
    rows = list(csv.reader(io.StringIO(result)))
    # header + 1 regression flag
    assert len(rows) == 2


def test_write_to_stream_json(report):
    buf = io.StringIO()
    write_regression_to_stream(report, buf, fmt="json")
    data = json.loads(buf.getvalue())
    assert data["query"] == QUERY


def test_write_to_stream_csv(report):
    buf = io.StringIO()
    write_regression_to_stream(report, buf, fmt="csv")
    assert "stage" in buf.getvalue()


def test_save_regression_json(report):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "out.json"
        save_regression(report, p, fmt="json")
        data = json.loads(p.read_text())
        assert data["query"] == QUERY


def test_save_regression_csv(report):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "out.csv"
        save_regression(report, p, fmt="csv")
        content = p.read_text()
        assert "stage" in content
