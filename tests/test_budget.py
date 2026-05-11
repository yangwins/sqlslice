"""Tests for sqlslice.budget module."""
import pytest

from sqlslice.budget import BudgetReport, BudgetViolation, QueryBudget
from sqlslice.profiler import ProfileResult, Stage


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def stages():
    return [
        Stage("parse", 10.0),
        Stage("plan", 50.0),
        Stage("execute", 200.0),
        Stage("fetch", 30.0),
    ]


@pytest.fixture()
def result(stages):
    return ProfileResult(
        query="SELECT * FROM orders",
        stages=stages,
        error=None,
    )


@pytest.fixture()
def budget():
    return QueryBudget({"parse": 20.0, "plan": 40.0, "execute": 150.0, "fetch": 50.0})


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_empty_budgets_raises():
    with pytest.raises(ValueError, match="must not be empty"):
        QueryBudget({})


def test_non_positive_budget_raises():
    with pytest.raises(ValueError, match="must be positive"):
        QueryBudget({"parse": 0.0})


def test_negative_budget_raises():
    with pytest.raises(ValueError, match="must be positive"):
        QueryBudget({"parse": -5.0})


# ---------------------------------------------------------------------------
# BudgetReport basics
# ---------------------------------------------------------------------------

def test_check_returns_budget_report(budget, result):
    report = budget.check(result)
    assert isinstance(report, BudgetReport)


def test_report_query_matches(budget, result):
    report = budget.check(result)
    assert report.query == result.query


def test_violations_detected(budget, result):
    report = budget.check(result)
    # plan (50 > 40) and execute (200 > 150) should violate
    assert report.has_violations
    violated_names = {v.stage_name for v in report.violations}
    assert "plan" in violated_names
    assert "execute" in violated_names


def test_no_violation_for_within_budget_stage(budget, result):
    report = budget.check(result)
    violated_names = {v.stage_name for v in report.violations}
    assert "parse" not in violated_names
    assert "fetch" not in violated_names


def test_total_excess_ms(budget, result):
    report = budget.check(result)
    expected = (50.0 - 40.0) + (200.0 - 150.0)
    assert abs(report.total_excess_ms - expected) < 1e-6


# ---------------------------------------------------------------------------
# Unchecked stages
# ---------------------------------------------------------------------------

def test_unchecked_stages_when_budget_stage_missing(result):
    b = QueryBudget({"parse": 20.0, "missing_stage": 10.0})
    report = b.check(result)
    assert "missing_stage" in report.unchecked_stages


def test_no_unchecked_when_all_stages_present(budget, result):
    report = budget.check(result)
    assert report.unchecked_stages == []


# ---------------------------------------------------------------------------
# BudgetViolation repr
# ---------------------------------------------------------------------------

def test_violation_repr():
    v = BudgetViolation(stage_name="execute", budget_ms=150.0, actual_ms=200.0)
    r = repr(v)
    assert "execute" in r
    assert "150.00" in r
    assert "200.00" in r
    assert "50.00" in r


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def test_summary_contains_query(budget, result):
    report = budget.check(result)
    assert result.query in report.summary()


def test_summary_no_violations_message():
    b = QueryBudget({"parse": 100.0})
    r = ProfileResult(query="Q", stages=[Stage("parse", 5.0)], error=None)
    report = b.check(r)
    assert "within budget" in report.summary()


def test_summary_lists_violation_stage(budget, result):
    report = budget.check(result)
    assert "execute" in report.summary()
