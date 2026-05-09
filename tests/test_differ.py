"""Tests for sqlslice.differ module."""

import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.differ import ProfileDiffer, DiffReport, StageTrend


SELECT_SQL = "SELECT * FROM orders"


def _make_result(parse=0.1, execute=0.5, fetch=0.2, error=None):
    stages = [
        Stage("parse", parse),
        Stage("execute", execute),
        Stage("fetch", fetch),
    ]
    return ProfileResult(query=SELECT_SQL, stages=stages, error=error)


@pytest.fixture
def differ():
    return ProfileDiffer()


def test_add_and_diff_returns_report(differ):
    differ.add(_make_result())
    differ.add(_make_result(execute=0.8))
    report = differ.diff()
    assert isinstance(report, DiffReport)


def test_diff_run_count(differ):
    for _ in range(4):
        differ.add(_make_result())
    report = differ.diff()
    assert report.run_count == 4


def test_diff_query_name(differ):
    differ.add(_make_result())
    report = differ.diff()
    assert report.query == SELECT_SQL


def test_diff_stage_trends_count(differ):
    differ.add(_make_result())
    differ.add(_make_result())
    report = differ.diff()
    assert len(report.stage_trends) == 3


def test_stage_trend_mean(differ):
    differ.add(_make_result(execute=0.4))
    differ.add(_make_result(execute=0.6))
    report = differ.diff()
    exec_trend = next(t for t in report.stage_trends if t.stage_name == "execute")
    assert abs(exec_trend.mean - 0.5) < 1e-9


def test_stage_trend_min_max(differ):
    differ.add(_make_result(execute=0.2))
    differ.add(_make_result(execute=0.9))
    report = differ.diff()
    exec_trend = next(t for t in report.stage_trends if t.stage_name == "execute")
    assert exec_trend.min == pytest.approx(0.2)
    assert exec_trend.max == pytest.approx(0.9)


def test_stage_trend_rising():
    st = StageTrend("execute", durations=[0.1, 0.1, 0.5, 0.5])
    assert st.trend == "rising"


def test_stage_trend_falling():
    st = StageTrend("execute", durations=[0.5, 0.5, 0.1, 0.1])
    assert st.trend == "falling"


def test_stage_trend_stable():
    st = StageTrend("execute", durations=[0.3, 0.3, 0.3, 0.3])
    assert st.trend == "stable"


def test_stage_trend_single_sample():
    st = StageTrend("execute", durations=[0.5])
    assert st.trend == "stable"


def test_diff_errors_tracked(differ):
    differ.add(_make_result())
    differ.add(_make_result(error="timeout"))
    report = differ.diff()
    assert sum(1 for e in report.errors if e is not None) == 1


def test_diff_no_results_raises(differ):
    with pytest.raises(ValueError, match="No results"):
        differ.diff()


def test_add_invalid_type_raises(differ):
    with pytest.raises(TypeError):
        differ.add("not a result")


def test_diff_report_summary_contains_query(differ):
    differ.add(_make_result())
    report = differ.diff()
    assert SELECT_SQL in report.summary()


def test_diff_report_summary_shows_stage_names(differ):
    differ.add(_make_result())
    report = differ.diff()
    summary = report.summary()
    assert "execute" in summary
    assert "parse" in summary


def test_diff_report_repr(differ):
    differ.add(_make_result())
    report = differ.diff()
    assert "DiffReport" in repr(report)


def test_stage_trend_repr():
    st = StageTrend("fetch", durations=[0.1, 0.2])
    assert "StageTrend" in repr(st)
    assert "fetch" in repr(st)
