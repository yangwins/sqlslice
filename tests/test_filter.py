"""Tests for sqlslice.filter module."""

import pytest
from sqlslice.profiler import ProfileResult, Stage
from sqlslice.filter import ProfileFilter, FilteredResult


@pytest.fixture
def stages():
    return [
        Stage(name="parse", duration=0.05),
        Stage(name="plan", duration=0.20),
        Stage(name="execute", duration=1.50),
        Stage(name="fetch", duration=0.30),
    ]


@pytest.fixture
def result(stages):
    return ProfileResult(query="SELECT * FROM orders", stages=stages)


@pytest.fixture
def pfilter():
    return ProfileFilter()


def test_apply_returns_filtered_result(result, pfilter):
    fr = pfilter.apply(result)
    assert isinstance(fr, FilteredResult)


def test_no_predicates_returns_all_stages(result, pfilter):
    fr = pfilter.apply(result)
    assert len(fr.stages) == 4


def test_min_duration_filters_stages(result, pfilter):
    fr = pfilter.min_duration(0.25).apply(result)
    assert len(fr.stages) == 2
    assert all(s.duration >= 0.25 for s in fr.stages)


def test_min_duration_negative_raises(pfilter):
    with pytest.raises(ValueError, match="non-negative"):
        pfilter.min_duration(-0.1)


def test_name_contains_filters_stages(result, pfilter):
    fr = pfilter.name_contains("e").apply(result)
    names = [s.name for s in fr.stages]
    assert "parse" in names
    assert "execute" in names
    assert "fetch" in names
    assert "plan" not in names


def test_name_contains_case_insensitive(result, pfilter):
    fr = pfilter.name_contains("EXECUTE").apply(result)
    assert len(fr.stages) == 1
    assert fr.stages[0].name == "execute"


def test_name_in_filters_stages(result, pfilter):
    fr = pfilter.name_in(["parse", "fetch"]).apply(result)
    assert len(fr.stages) == 2
    assert {s.name for s in fr.stages} == {"parse", "fetch"}


def test_custom_predicate(result, pfilter):
    fr = pfilter.custom(lambda s: s.duration > 1.0).apply(result)
    assert len(fr.stages) == 1
    assert fr.stages[0].name == "execute"


def test_combined_predicates(result, pfilter):
    fr = pfilter.min_duration(0.10).name_contains("e").apply(result)
    names = [s.name for s in fr.stages]
    assert "execute" in names
    assert "fetch" in names
    assert "parse" not in names  # duration 0.05 < 0.10


def test_total_duration_is_sum_of_filtered(result, pfilter):
    fr = pfilter.min_duration(0.25).apply(result)
    expected = sum(s.duration for s in fr.stages)
    assert fr.total_duration == pytest.approx(expected)


def test_filtered_result_summary_contains_query(result, pfilter):
    fr = pfilter.apply(result)
    assert "SELECT * FROM orders" in fr.summary()


def test_filtered_result_repr(result, pfilter):
    fr = pfilter.apply(result)
    r = repr(fr)
    assert "FilteredResult" in r
    assert "stages=4" in r


def test_reset_clears_predicates(result, pfilter):
    pfilter.min_duration(1.0)
    pfilter.reset()
    fr = pfilter.apply(result)
    assert len(fr.stages) == 4


def test_empty_result_after_strict_filter(result, pfilter):
    fr = pfilter.min_duration(99.0).apply(result)
    assert len(fr.stages) == 0
    assert fr.total_duration == 0.0
