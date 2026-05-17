"""Tests for sqlslice.flattener."""

import pytest
from sqlslice.profiler import ProfileResult, Stage
from sqlslice.flattener import FlatStage, FlatReport, QueryFlattener


@pytest.fixture
def stages():
    return [
        Stage(name="parse", duration_ms=10.0),
        Stage(name="plan", duration_ms=20.0),
        Stage(name="execute", duration_ms=50.0),
        Stage(name="parse", duration_ms=5.0),   # duplicate
        Stage(name="execute", duration_ms=30.0), # duplicate
    ]


@pytest.fixture
def result(stages):
    return ProfileResult(query="SELECT 1", stages=stages, error=None)


@pytest.fixture
def flattener():
    return QueryFlattener()


def test_flatten_returns_flat_report(flattener, result):
    report = flattener.flatten(result)
    assert isinstance(report, FlatReport)


def test_flat_report_query_preserved(flattener, result):
    report = flattener.flatten(result)
    assert report.query == "SELECT 1"


def test_original_stage_count(flattener, result, stages):
    report = flattener.flatten(result)
    assert report.original_stage_count == len(stages)


def test_unique_stage_count(flattener, result):
    report = flattener.flatten(result)
    # parse, plan, execute → 3 unique
    assert len(report.flat_stages) == 3


def test_duplicate_durations_summed(flattener, result):
    report = flattener.flatten(result)
    parse_stage = next(s for s in report.flat_stages if s.name == "parse")
    assert parse_stage.total_duration_ms == pytest.approx(15.0)


def test_duplicate_call_count(flattener, result):
    report = flattener.flatten(result)
    execute_stage = next(s for s in report.flat_stages if s.name == "execute")
    assert execute_stage.call_count == 2


def test_single_stage_call_count(flattener, result):
    report = flattener.flatten(result)
    plan_stage = next(s for s in report.flat_stages if s.name == "plan")
    assert plan_stage.call_count == 1


def test_avg_duration_ms(flattener, result):
    report = flattener.flatten(result)
    execute_stage = next(s for s in report.flat_stages if s.name == "execute")
    assert execute_stage.avg_duration_ms() == pytest.approx(40.0)


def test_flat_stage_repr():
    fs = FlatStage(name="plan", total_duration_ms=20.0, call_count=1)
    r = repr(fs)
    assert "plan" in r
    assert "20.00" in r
    assert "calls=1" in r


def test_flat_report_repr(flattener, result):
    report = flattener.flatten(result)
    r = repr(report)
    assert "FlatReport" in r
    assert "SELECT 1" in r


def test_summary_contains_query(flattener, result):
    report = flattener.flatten(result)
    assert "SELECT 1" in report.summary()


def test_summary_contains_stage_name(flattener, result):
    report = flattener.flatten(result)
    assert "execute" in report.summary()


def test_flatten_raises_on_non_result(flattener):
    with pytest.raises(TypeError):
        flattener.flatten("not a result")


def test_no_duplicates_passthrough(flattener):
    unique_stages = [
        Stage(name="parse", duration_ms=10.0),
        Stage(name="plan", duration_ms=20.0),
    ]
    r = ProfileResult(query="SELECT 2", stages=unique_stages, error=None)
    report = flattener.flatten(r)
    assert report.original_stage_count == len(report.flat_stages)
