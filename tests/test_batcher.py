"""Tests for sqlslice.batcher."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from sqlslice.batcher import BatchEntry, BatchReport, QueryBatcher
from sqlslice.profiler import ProfileResult, Stage


def _make_result(query: str, durations: list[float]) -> ProfileResult:
    stages = [
        Stage(name=f"stage{i}", duration_ms=d)
        for i, d in enumerate(durations)
    ]
    return ProfileResult(query=query, stages=stages)


@pytest.fixture()
def mock_profiler():
    p = MagicMock()
    p.profile.side_effect = [
        _make_result("SELECT 1", [10.0, 20.0]),
        _make_result("SELECT 2", [5.0]),
    ]
    return p


@pytest.fixture()
def batcher(mock_profiler):
    return QueryBatcher(profiler=mock_profiler)


QUERIES = [("q1", "SELECT 1"), ("q2", "SELECT 2")]


def test_run_returns_batch_report(batcher):
    report = batcher.run(QUERIES)
    assert isinstance(report, BatchReport)


def test_run_total_count(batcher):
    report = batcher.run(QUERIES)
    assert report.total_count == 2


def test_run_success_count(batcher):
    report = batcher.run(QUERIES)
    assert report.success_count == 2


def test_run_failure_count_zero_when_all_succeed(batcher):
    report = batcher.run(QUERIES)
    assert report.failure_count == 0


def test_run_total_duration_ms(batcher):
    report = batcher.run(QUERIES)
    assert report.total_duration_ms == pytest.approx(35.0)


def test_run_entry_names(batcher):
    report = batcher.run(QUERIES)
    names = [e.name for e in report.entries]
    assert names == ["q1", "q2"]


def test_run_entries_succeeded(batcher):
    report = batcher.run(QUERIES)
    assert all(e.succeeded for e in report.entries)


def test_run_failure_recorded_on_profiler_exception():
    p = MagicMock()
    p.profile.side_effect = RuntimeError("db is down")
    batcher = QueryBatcher(profiler=p)
    report = batcher.run([("bad", "SELECT boom")])
    assert report.failure_count == 1
    assert report.success_count == 0
    assert report.entries[0].error == "db is down"


def test_run_mixed_success_and_failure():
    p = MagicMock()
    p.profile.side_effect = [
        _make_result("SELECT 1", [10.0]),
        RuntimeError("timeout"),
    ]
    batcher = QueryBatcher(profiler=p)
    report = batcher.run([("ok", "SELECT 1"), ("bad", "SELECT boom")])
    assert report.success_count == 1
    assert report.failure_count == 1


def test_run_empty_queries_raises(batcher):
    with pytest.raises(ValueError, match="empty"):
        batcher.run([])


def test_none_profiler_raises():
    with pytest.raises(ValueError, match="profiler"):
        QueryBatcher(profiler=None)


def test_on_entry_callback_called_for_each(batcher):
    seen = []
    batcher.run(QUERIES, on_entry=seen.append)
    assert len(seen) == 2
    assert all(isinstance(e, BatchEntry) for e in seen)


def test_batch_report_summary_contains_query_names(batcher):
    report = batcher.run(QUERIES)
    summary = report.summary()
    assert "q1" in summary
    assert "q2" in summary


def test_batch_report_summary_contains_totals(batcher):
    report = batcher.run(QUERIES)
    summary = report.summary()
    assert "35.00" in summary


def test_batch_entry_repr_ok():
    entry = BatchEntry(name="myq", query="SELECT 1", result=_make_result("SELECT 1", [5.0]))
    assert "ok" in repr(entry)
    assert "myq" in repr(entry)


def test_batch_entry_repr_error():
    entry = BatchEntry(name="myq", query="SELECT 1", error="boom")
    assert "error" in repr(entry)


def test_batch_report_repr():
    entry = BatchEntry(name="q", query="SELECT 1", result=_make_result("SELECT 1", [1.0]))
    report = BatchReport(entries=[entry])
    r = repr(report)
    assert "BatchReport" in r
    assert "total=1" in r
