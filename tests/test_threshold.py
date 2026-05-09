"""Tests for sqlslice.threshold."""

import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.threshold import ThresholdChecker, ThresholdReport, ThresholdViolation


@pytest.fixture()
def stages():
    return [
        Stage(name="parse", duration_ms=10.0),
        Stage(name="plan", duration_ms=50.0),
        Stage(name="execute", duration_ms=200.0),
    ]


@pytest.fixture()
def result(stages):
    return ProfileResult(
        query="SELECT * FROM orders",
        stages=stages,
        total_duration_ms=260.0,
    )


@pytest.fixture()
def checker():
    return ThresholdChecker(
        stage_limits={"parse": 20.0, "execute": 100.0},
        total_limit_ms=300.0,
    )


def test_check_returns_threshold_report(checker, result):
    report = checker.check(result)
    assert isinstance(report, ThresholdReport)


def test_no_violations_when_all_under_limit(result):
    checker = ThresholdChecker(stage_limits={"execute": 500.0}, total_limit_ms=500.0)
    report = checker.check(result)
    assert not report.has_violations
    assert report.violations == []


def test_stage_violation_detected(checker, result):
    report = checker.check(result)
    names = [v.stage_name for v in report.violations]
    assert "execute" in names


def test_stage_within_limit_not_flagged(checker, result):
    report = checker.check(result)
    names = [v.stage_name for v in report.violations]
    assert "parse" not in names


def test_violation_excess_ms(checker, result):
    report = checker.check(result)
    exec_violation = next(v for v in report.violations if v.stage_name == "execute")
    assert exec_violation.excess_ms == pytest.approx(100.0)


def test_total_not_exceeded_when_under_limit(checker, result):
    report = checker.check(result)
    assert not report.total_exceeded


def test_total_exceeded_when_over_limit(result):
    checker = ThresholdChecker(total_limit_ms=100.0)
    report = checker.check(result)
    assert report.total_exceeded
    assert report.has_violations


def test_no_total_limit_does_not_set_exceeded(result):
    checker = ThresholdChecker()
    report = checker.check(result)
    assert not report.total_exceeded
    assert report.total_limit_ms is None


def test_invalid_total_limit_raises():
    with pytest.raises(ValueError, match="positive"):
        ThresholdChecker(total_limit_ms=-1.0)


def test_summary_contains_query(checker, result):
    report = checker.check(result)
    assert result.query in report.summary()


def test_summary_shows_exceeded_label(result):
    checker = ThresholdChecker(total_limit_ms=50.0)
    report = checker.check(result)
    assert "EXCEEDED" in report.summary()


def test_summary_no_violations_message(result):
    checker = ThresholdChecker()
    report = checker.check(result)
    assert "No threshold violations" in report.summary()


def test_violation_repr_contains_stage_name():
    v = ThresholdViolation(stage_name="plan", duration_ms=80.0, limit_ms=40.0)
    assert "plan" in repr(v)
