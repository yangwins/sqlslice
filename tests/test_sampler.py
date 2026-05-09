"""Tests for sqlslice.sampler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.sampler import QuerySampler, SamplePoint, SamplerReport


def _make_result(query: str = "SELECT 1", total: float = 0.1, error=None) -> ProfileResult:
    stages = [Stage(name="execute", duration=total)]
    return ProfileResult(query=query, stages=stages, error=error)


@pytest.fixture()
def sampler() -> QuerySampler:
    return QuerySampler(interval=0.0)


# ---------------------------------------------------------------------------
# QuerySampler construction
# ---------------------------------------------------------------------------

def test_invalid_interval_raises():
    with pytest.raises(ValueError, match="interval must be positive"):
        QuerySampler(interval=0)


def test_negative_interval_raises():
    with pytest.raises(ValueError):
        QuerySampler(interval=-1.0)


# ---------------------------------------------------------------------------
# sample() basic behaviour
# ---------------------------------------------------------------------------

def test_sample_returns_sampler_report(sampler):
    fn = MagicMock(return_value=_make_result())
    report = sampler.sample(fn, count=3)
    assert isinstance(report, SamplerReport)


def test_sample_count_matches_requested(sampler):
    fn = MagicMock(return_value=_make_result())
    report = sampler.sample(fn, count=4)
    assert report.sample_count == 4


def test_sample_query_taken_from_first_result(sampler):
    fn = MagicMock(return_value=_make_result(query="SELECT version()"))
    report = sampler.sample(fn, count=2)
    assert report.query == "SELECT version()"


def test_sample_count_zero_raises(sampler):
    fn = MagicMock(return_value=_make_result())
    with pytest.raises(ValueError, match="count must be at least 1"):
        sampler.sample(fn, count=0)


def test_on_sample_callback_called_for_each(sampler):
    fn = MagicMock(return_value=_make_result())
    collected = []
    sampler.sample(fn, count=3, on_sample=collected.append)
    assert len(collected) == 3
    assert all(isinstance(p, SamplePoint) for p in collected)


# ---------------------------------------------------------------------------
# SamplerReport statistics
# ---------------------------------------------------------------------------

def test_successful_samples_excludes_errors(sampler):
    results = [
        _make_result(total=0.1),
        _make_result(total=0.2, error=RuntimeError("boom")),
        _make_result(total=0.3),
    ]
    fn = MagicMock(side_effect=results)
    report = sampler.sample(fn, count=3)
    assert len(report.successful_samples) == 2
    assert len(report.failed_samples) == 1


def test_average_duration_correct(sampler):
    results = [_make_result(total=d) for d in [0.1, 0.3]]
    fn = MagicMock(side_effect=results)
    report = sampler.sample(fn, count=2)
    assert report.average_duration == pytest.approx(0.2)


def test_peak_duration_correct(sampler):
    results = [_make_result(total=d) for d in [0.05, 0.9, 0.4]]
    fn = MagicMock(side_effect=results)
    report = sampler.sample(fn, count=3)
    assert report.peak_duration == pytest.approx(0.9)


def test_average_duration_none_when_all_errors(sampler):
    fn = MagicMock(return_value=_make_result(error=RuntimeError("oops")))
    report = sampler.sample(fn, count=2)
    assert report.average_duration is None
    assert report.peak_duration is None


# ---------------------------------------------------------------------------
# SamplerReport.summary
# ---------------------------------------------------------------------------

def test_summary_contains_query(sampler):
    fn = MagicMock(return_value=_make_result(query="SELECT now()"))
    report = sampler.sample(fn, count=1)
    assert "SELECT now()" in report.summary()


def test_summary_contains_sample_counts(sampler):
    results = [_make_result(total=0.1), _make_result(error=RuntimeError("x"))]
    fn = MagicMock(side_effect=results)
    report = sampler.sample(fn, count=2)
    summary = report.summary()
    assert "2 total" in summary
    assert "1 ok" in summary
    assert "1 failed" in summary


# ---------------------------------------------------------------------------
# SamplePoint repr
# ---------------------------------------------------------------------------

def test_sample_point_repr_ok(sampler):
    fn = MagicMock(return_value=_make_result())
    report = sampler.sample(fn, count=1)
    assert "ok" in repr(report.samples[0])


def test_sample_point_repr_error(sampler):
    fn = MagicMock(return_value=_make_result(error=RuntimeError("bad")))
    report = sampler.sample(fn, count=1)
    assert "error" in repr(report.samples[0])
