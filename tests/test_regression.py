"""Tests for sqlslice.regression."""
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.regression import RegressionDetector, RegressionFlag, RegressionReport

QUERY = "SELECT * FROM orders"


def _make_result(parse=10.0, plan=5.0, execute=100.0, query=QUERY):
    stages = [
        Stage("parse", parse),
        Stage("plan", plan),
        Stage("execute", execute),
    ]
    return ProfileResult(query=query, stages=stages)


@pytest.fixture
def detector():
    return RegressionDetector(threshold_pct=10.0)


@pytest.fixture
def baseline():
    return _make_result(parse=10.0, plan=5.0, execute=100.0)


@pytest.fixture
def current_no_regression():
    return _make_result(parse=10.5, plan=5.1, execute=101.0)


@pytest.fixture
def current_with_regression():
    return _make_result(parse=10.0, plan=5.0, execute=150.0)


def test_detect_returns_regression_report(detector, baseline, current_no_regression):
    report = detector.detect(baseline, current_no_regression)
    assert isinstance(report, RegressionReport)


def test_no_regressions_when_under_threshold(detector, baseline, current_no_regression):
    report = detector.detect(baseline, current_no_regression)
    assert not report.has_regressions
    assert report.flags == []


def test_regression_flagged_when_over_threshold(detector, baseline, current_with_regression):
    report = detector.detect(baseline, current_with_regression)
    assert report.has_regressions
    assert len(report.flags) == 1
    assert report.flags[0].stage_name == "execute"


def test_regression_flag_values(detector, baseline, current_with_regression):
    report = detector.detect(baseline, current_with_regression)
    flag = report.flags[0]
    assert flag.baseline_ms == pytest.approx(100.0)
    assert flag.current_ms == pytest.approx(150.0)
    assert flag.delta_ms == pytest.approx(50.0)
    assert flag.pct_change == pytest.approx(50.0)


def test_report_query_name(detector, baseline, current_with_regression):
    report = detector.detect(baseline, current_with_regression)
    assert report.query == QUERY


def test_report_threshold_stored(detector, baseline, current_no_regression):
    report = detector.detect(baseline, current_no_regression)
    assert report.threshold_pct == 10.0


def test_summary_no_regressions(detector, baseline, current_no_regression):
    report = detector.detect(baseline, current_no_regression)
    summary = report.summary()
    assert "no regressions" in summary
    assert QUERY in summary


def test_summary_with_regressions(detector, baseline, current_with_regression):
    report = detector.detect(baseline, current_with_regression)
    summary = report.summary()
    assert "execute" in summary
    assert "150" in summary or "150.00" in summary


def test_invalid_threshold_raises():
    with pytest.raises(ValueError):
        RegressionDetector(threshold_pct=0)


def test_negative_threshold_raises():
    with pytest.raises(ValueError):
        RegressionDetector(threshold_pct=-5.0)


def test_stage_missing_in_baseline_is_skipped(detector):
    base = ProfileResult(query=QUERY, stages=[Stage("parse", 10.0)])
    cur = ProfileResult(
        query=QUERY, stages=[Stage("parse", 10.0), Stage("execute", 200.0)]
    )
    report = detector.detect(base, cur)
    assert not report.has_regressions


def test_regression_flag_repr():
    flag = RegressionFlag("execute", 100.0, 150.0, 50.0, 50.0)
    r = repr(flag)
    assert "execute" in r
    assert "50.0" in r or "50.00" in r
