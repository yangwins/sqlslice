"""Tests for sqlslice.watchdog module."""

import pytest
from sqlslice.profiler import ProfileResult, Stage
from sqlslice.watchdog import QueryWatchdog, WatchdogAlert, WatchdogReport


def _make_result(query: str, durations: list) -> ProfileResult:
    stages = [Stage(name=f"stage_{i}", duration=d) for i, d in enumerate(durations)]
    return ProfileResult(query=query, stages=stages, error=None)


@pytest.fixture
def results_under():
    return [_make_result("SELECT 1", [0.01, 0.02]) for _ in range(3)]


@pytest.fixture
def results_mixed():
    return [
        _make_result("SELECT 1", [0.01, 0.02]),   # 0.03 — under
        _make_result("SELECT 1", [0.10, 0.20]),   # 0.30 — over
        _make_result("SELECT 1", [0.05, 0.06]),   # 0.11 — under
        _make_result("SELECT 1", [0.50, 0.60]),   # 1.10 — over
    ]


@pytest.fixture
def watchdog():
    return QueryWatchdog(threshold=0.15)


def test_watchdog_invalid_threshold():
    with pytest.raises(ValueError, match="threshold"):
        QueryWatchdog(threshold=0)


def test_watchdog_empty_results(watchdog):
    with pytest.raises(ValueError, match="empty"):
        watchdog.watch([])


def test_watch_returns_watchdog_report(watchdog, results_under):
    report = watchdog.watch(results_under)
    assert isinstance(report, WatchdogReport)


def test_no_alerts_when_all_under_threshold(watchdog, results_under):
    report = watchdog.watch(results_under)
    assert report.alert_count == 0


def test_clean_runs_equals_total_when_no_alerts(watchdog, results_under):
    report = watchdog.watch(results_under)
    assert report.clean_runs == report.total_runs


def test_alerts_fired_for_over_threshold_runs(watchdog, results_mixed):
    report = watchdog.watch(results_mixed)
    assert report.alert_count == 2


def test_alert_run_index_is_correct(watchdog, results_mixed):
    report = watchdog.watch(results_mixed)
    assert report.alerts[0].run_index == 1
    assert report.alerts[1].run_index == 3


def test_alert_total_duration(watchdog, results_mixed):
    report = watchdog.watch(results_mixed)
    assert abs(report.alerts[0].total_duration - 0.30) < 1e-9


def test_alert_repr_contains_run_index(watchdog, results_mixed):
    report = watchdog.watch(results_mixed)
    assert "run=1" in repr(report.alerts[0])


def test_on_alert_callback_called(results_mixed):
    fired = []
    wd = QueryWatchdog(threshold=0.15, on_alert=lambda a: fired.append(a))
    wd.watch(results_mixed)
    assert len(fired) == 2
    assert all(isinstance(a, WatchdogAlert) for a in fired)


def test_report_query_name(watchdog, results_mixed):
    report = watchdog.watch(results_mixed)
    assert report.query == "SELECT 1"


def test_report_total_runs(watchdog, results_mixed):
    report = watchdog.watch(results_mixed)
    assert report.total_runs == 4


def test_report_summary_contains_threshold(watchdog, results_under):
    report = watchdog.watch(results_under)
    assert "0.1500" in report.summary()


def test_report_summary_contains_alert_lines(watchdog, results_mixed):
    report = watchdog.watch(results_mixed)
    summary = report.summary()
    assert "[!]" in summary
    assert summary.count("[!]") == 2
