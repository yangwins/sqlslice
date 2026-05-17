"""Tests for sqlslice.trimmer."""
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.trimmer import StageTrimmer, TrimReport


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def stages():
    return [
        Stage(name="parse", duration_ms=0.4),
        Stage(name="plan", duration_ms=2.1),
        Stage(name="execute", duration_ms=55.0),
        Stage(name="fetch", duration_ms=0.8),
    ]


@pytest.fixture()
def result(stages):
    return ProfileResult(query="SELECT 1", stages=stages, total_duration_ms=58.3)


@pytest.fixture()
def trimmer():
    return StageTrimmer(min_duration_ms=1.0)


# ---------------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------------

def test_invalid_zero_raises():
    with pytest.raises(ValueError):
        StageTrimmer(min_duration_ms=0)


def test_negative_raises():
    with pytest.raises(ValueError):
        StageTrimmer(min_duration_ms=-5.0)


def test_non_numeric_raises():
    with pytest.raises(TypeError):
        StageTrimmer(min_duration_ms="fast")


# ---------------------------------------------------------------------------
# trim() basics
# ---------------------------------------------------------------------------

def test_trim_returns_trim_report(trimmer, result):
    report = trimmer.trim(result)
    assert isinstance(report, TrimReport)


def test_trim_requires_profile_result(trimmer):
    with pytest.raises(TypeError):
        trimmer.trim("not a result")


def test_kept_stages_above_threshold(trimmer, result):
    report = trimmer.trim(result)
    assert all(s.duration_ms >= 1.0 for s in report.kept)


def test_removed_stages_below_threshold(trimmer, result):
    report = trimmer.trim(result)
    assert all(s.duration_ms < 1.0 for s in report.removed)


def test_kept_count(trimmer, result):
    report = trimmer.trim(result)
    # plan (2.1) and execute (55.0) survive
    assert report.kept_count == 2


def test_removed_count(trimmer, result):
    report = trimmer.trim(result)
    # parse (0.4) and fetch (0.8) are dropped
    assert report.removed_count == 2


def test_query_preserved(trimmer, result):
    report = trimmer.trim(result)
    assert report.query == "SELECT 1"


def test_total_kept_ms(trimmer, result):
    report = trimmer.trim(result)
    assert abs(report.total_kept_ms - 57.1) < 0.01


def test_all_kept_when_threshold_very_low(result):
    t = StageTrimmer(min_duration_ms=0.1)
    report = t.trim(result)
    assert report.kept_count == 4
    assert report.removed_count == 0


def test_all_removed_when_threshold_very_high(result):
    t = StageTrimmer(min_duration_ms=1000.0)
    report = t.trim(result)
    assert report.kept_count == 0
    assert report.removed_count == 4


def test_summary_contains_query(trimmer, result):
    report = trimmer.trim(result)
    assert "SELECT 1" in report.summary()


def test_summary_contains_removed_names(trimmer, result):
    report = trimmer.trim(result)
    summary = report.summary()
    assert "parse" in summary
    assert "fetch" in summary


def test_repr(trimmer, result):
    report = trimmer.trim(result)
    r = repr(report)
    assert "TrimReport" in r
    assert "kept=" in r
    assert "removed=" in r
