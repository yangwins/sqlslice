"""Tests for sqlslice.comparator module."""

import pytest
from sqlslice.profiler import ProfileResult, Stage
from sqlslice.comparator import QueryComparator, ComparisonReport, StageDiff


QUERY = "SELECT * FROM orders WHERE status = 'pending'"


@pytest.fixture
def baseline():
    return ProfileResult(
        query=QUERY,
        stages=[
            Stage(name="parse", duration=0.01),
            Stage(name="plan", duration=0.05),
            Stage(name="execute", duration=0.20),
        ],
        error=None,
    )


@pytest.fixture
def current_faster():
    return ProfileResult(
        query=QUERY,
        stages=[
            Stage(name="parse", duration=0.01),
            Stage(name="plan", duration=0.04),
            Stage(name="execute", duration=0.15),
        ],
        error=None,
    )


@pytest.fixture
def current_slower():
    return ProfileResult(
        query=QUERY,
        stages=[
            Stage(name="parse", duration=0.01),
            Stage(name="plan", duration=0.08),
            Stage(name="execute", duration=0.45),
        ],
        error=None,
    )


@pytest.fixture
def comparator():
    return QueryComparator()


def test_compare_returns_comparison_report(comparator, baseline, current_faster):
    report = comparator.compare(baseline, current_faster)
    assert isinstance(report, ComparisonReport)


def test_total_delta_improvement(comparator, baseline, current_faster):
    report = comparator.compare(baseline, current_faster)
    assert report.total_delta < 0


def test_total_delta_regression(comparator, baseline, current_slower):
    report = comparator.compare(baseline, current_slower)
    assert report.total_delta > 0


def test_is_regression_false_on_improvement(comparator, baseline, current_faster):
    report = comparator.compare(baseline, current_faster)
    assert report.is_regression is False


def test_is_regression_true_on_regression(comparator, baseline, current_slower):
    report = comparator.compare(baseline, current_slower)
    assert report.is_regression is True


def test_diffs_count_matches_stages(comparator, baseline, current_faster):
    report = comparator.compare(baseline, current_faster)
    assert len(report.diffs) == 3


def test_stage_diff_delta_correct(comparator, baseline, current_slower):
    report = comparator.compare(baseline, current_slower)
    execute_diff = next(d for d in report.diffs if d.stage_name == "execute")
    assert abs(execute_diff.delta - 0.25) < 1e-9


def test_stage_diff_pct_change(comparator, baseline, current_slower):
    report = comparator.compare(baseline, current_slower)
    execute_diff = next(d for d in report.diffs if d.stage_name == "execute")
    assert execute_diff.pct_change == pytest.approx(125.0)


def test_summary_contains_query(comparator, baseline, current_slower):
    report = comparator.compare(baseline, current_slower)
    assert QUERY in report.summary()


def test_summary_contains_stage_names(comparator, baseline, current_slower):
    report = comparator.compare(baseline, current_slower)
    summary = report.summary()
    for stage in ["parse", "plan", "execute"]:
        assert stage in summary


def test_missing_stage_in_current_gets_zero(comparator, baseline):
    current_missing = ProfileResult(
        query=QUERY,
        stages=[
            Stage(name="parse", duration=0.01),
            Stage(name="execute", duration=0.20),
        ],
        error=None,
    )
    report = comparator.compare(baseline, current_missing)
    plan_diff = next(d for d in report.diffs if d.stage_name == "plan")
    assert plan_diff.current_duration == 0.0
