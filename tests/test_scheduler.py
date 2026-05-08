"""Tests for sqlslice.scheduler."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from sqlslice.profiler import ProfileResult, QueryProfiler
from sqlslice.scheduler import QueryScheduler, ScheduleReport, ScheduledRun


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_result(total: float = 0.5, error=None) -> ProfileResult:
    result = MagicMock(spec=ProfileResult)
    result.total_duration = total
    result.error = error
    result.query = "SELECT 1"
    return result


@pytest.fixture()
def mock_profiler():
    profiler = MagicMock(spec=QueryProfiler)
    profiler.query = "SELECT 1"
    profiler.run.return_value = _make_result()
    return profiler


@pytest.fixture()
def scheduler(mock_profiler):
    return QueryScheduler(mock_profiler, interval=0.05, max_runs=3)


# ---------------------------------------------------------------------------
# ScheduledRun
# ---------------------------------------------------------------------------

def test_scheduled_run_repr():
    run = ScheduledRun(run_index=0, timestamp=time.time(), result=_make_result())
    assert "ScheduledRun" in repr(run)
    assert "#0" in repr(run)
    assert "ok" in repr(run)


def test_scheduled_run_repr_error():
    run = ScheduledRun(run_index=1, timestamp=time.time(), result=_make_result(error=RuntimeError("oops")))
    assert "error" in repr(run)


# ---------------------------------------------------------------------------
# ScheduleReport
# ---------------------------------------------------------------------------

def test_schedule_report_counts():
    runs = [
        ScheduledRun(0, time.time(), _make_result()),
        ScheduledRun(1, time.time(), _make_result(error=RuntimeError("fail"))),
        ScheduledRun(2, time.time(), _make_result(0.8)),
    ]
    report = ScheduleReport(query="SELECT 1", runs=runs)
    assert report.run_count == 3
    assert len(report.successful_runs) == 2
    assert len(report.failed_runs) == 1


def test_schedule_report_summary_contains_query():
    runs = [ScheduledRun(0, time.time(), _make_result(1.0))]
    report = ScheduleReport(query="SELECT 1", runs=runs)
    summary = report.summary()
    assert "SELECT 1" in summary
    assert "Total runs" in summary


def test_schedule_report_summary_avg_min_max():
    runs = [
        ScheduledRun(0, time.time(), _make_result(1.0)),
        ScheduledRun(1, time.time(), _make_result(3.0)),
    ]
    report = ScheduleReport(query="SELECT 1", runs=runs)
    summary = report.summary()
    assert "Avg" in summary
    assert "Min" in summary
    assert "Max" in summary


# ---------------------------------------------------------------------------
# QueryScheduler
# ---------------------------------------------------------------------------

def test_scheduler_invalid_interval(mock_profiler):
    with pytest.raises(ValueError, match="interval must be positive"):
        QueryScheduler(mock_profiler, interval=-1)


def test_run_once_returns_scheduled_run(scheduler, mock_profiler):
    run = scheduler.run_once()
    assert isinstance(run, ScheduledRun)
    assert run.run_index == 0
    mock_profiler.run.assert_called_once()


def test_run_once_increments_index(scheduler):
    r1 = scheduler.run_once()
    r2 = scheduler.run_once()
    assert r1.run_index == 0
    assert r2.run_index == 1


def test_on_result_callback_called(mock_profiler):
    callback = MagicMock()
    sched = QueryScheduler(mock_profiler, interval=0.05, max_runs=2, on_result=callback)
    sched.run_once()
    callback.assert_called_once()
    arg = callback.call_args[0][0]
    assert isinstance(arg, ScheduledRun)


def test_start_stop_collects_runs(mock_profiler):
    sched = QueryScheduler(mock_profiler, interval=0.02, max_runs=3)
    sched.start()
    # Give the background thread time to complete all max_runs
    time.sleep(0.3)
    report = sched.stop()
    assert isinstance(report, ScheduleReport)
    assert report.run_count == 3
    assert report.query == "SELECT 1"


def test_stop_without_start_returns_empty_report(mock_profiler):
    sched = QueryScheduler(mock_profiler, interval=1.0)
    report = sched.stop()
    assert report.run_count == 0
