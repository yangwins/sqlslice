"""Tests for sqlslice.export module."""

import csv
import io
import json
from pathlib import Path

import pytest

from sqlslice.export import save, to_csv, to_json, write_to_stream
from sqlslice.profiler import ProfileResult, Stage


@pytest.fixture()
def result() -> ProfileResult:
    stages = [
        Stage(name="parse", duration=0.02),
        Stage(name="execute", duration=0.48),
    ]
    return ProfileResult(query="SELECT id FROM users", stages=stages)


@pytest.fixture()
def result_with_error() -> ProfileResult:
    stages = [
        Stage(name="parse", duration=0.01),
        Stage(name="execute", duration=0.0, error="connection reset"),
    ]
    return ProfileResult(query="SELECT 1", stages=stages)


# --- to_json ---

def test_to_json_is_valid_json(result):
    data = json.loads(to_json(result))
    assert data["query"] == "SELECT id FROM users"


def test_to_json_total_duration(result):
    data = json.loads(to_json(result))
    assert abs(data["total_duration"] - 0.50) < 1e-9


def test_to_json_stage_count(result):
    data = json.loads(to_json(result))
    assert len(data["stages"]) == 2


def test_to_json_share_values(result):
    data = json.loads(to_json(result))
    shares = [s["share"] for s in data["stages"]]
    assert abs(sum(shares) - 100.0) < 0.1


def test_to_json_error_field(result_with_error):
    data = json.loads(to_json(result_with_error))
    errors = {s["name"]: s["error"] for s in data["stages"]}
    assert errors["execute"] == "connection reset"
    assert errors["parse"] is None


# --- to_csv ---

def test_to_csv_has_header(result):
    rows = list(csv.DictReader(io.StringIO(to_csv(result))))
    assert "stage" in rows[0]


def test_to_csv_row_count(result):
    rows = list(csv.DictReader(io.StringIO(to_csv(result))))
    assert len(rows) == 2


def test_to_csv_error_column(result_with_error):
    rows = list(csv.DictReader(io.StringIO(to_csv(result_with_error))))
    execute_row = next(r for r in rows if r["stage"] == "execute")
    assert execute_row["error"] == "connection reset"


# --- save ---

def test_save_json(tmp_path, result):
    out = save(result, tmp_path / "report.json", fmt="json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["query"] == result.query


def test_save_csv(tmp_path, result):
    out = save(result, tmp_path / "report.csv", fmt="csv")
    assert out.exists()
    rows = list(csv.DictReader(io.StringIO(out.read_text())))
    assert len(rows) == 2


def test_save_unknown_format(tmp_path, result):
    with pytest.raises(ValueError, match="Unsupported export format"):
        save(result, tmp_path / "report.xml", fmt="xml")


# --- write_to_stream ---

def test_write_to_stream_json(result):
    buf = io.StringIO()
    write_to_stream(result, buf, fmt="json")
    data = json.loads(buf.getvalue())
    assert data["query"] == result.query


def test_write_to_stream_csv(result):
    buf = io.StringIO()
    write_to_stream(result, buf, fmt="csv")
    rows = list(csv.DictReader(io.StringIO(buf.getvalue())))
    assert len(rows) == 2
