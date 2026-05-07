"""Tests for sqlslice/reporter.py"""

import pytest
from sqlslice.profiler import ProfileResult, Stage
from sqlslice.reporter import Report, QueryReporter


@pytest.fixture
def stages():
    return [
        Stage(name="parse", duration_ms=10.0),
        Stage(name="plan", duration_ms=5.0),
        Stage(name="execute", duration_ms=85.0),
    ]


@pytest.fixture
def profile(stages):
    return ProfileResult(query="SELECT * FROM orders", stages=stages)


@pytest.fixture
def reporter():
    return QueryReporter(fmt="text", threshold=0.2, analyze=True)


def test_generate_returns_report(reporter, profile):
    report = reporter.generate(profile)
    assert isinstance(report, Report)


def test_report_has_profile(reporter, profile):
    report = reporter.generate(profile)
    assert report.profile is profile


def test_report_has_analysis_when_enabled(reporter, profile):
    report = reporter.generate(profile)
    assert report.analysis is not None


def test_report_no_analysis_when_disabled(profile):
    reporter = QueryReporter(fmt="text", analyze=False)
    report = reporter.generate(profile)
    assert report.analysis is None


def test_render_returns_string(reporter, profile):
    report = reporter.generate(profile)
    rendered = report.render()
    assert isinstance(rendered, str)
    assert "SELECT * FROM orders" in rendered


def test_render_includes_analysis_summary(reporter, profile):
    report = reporter.generate(profile)
    rendered = report.render()
    assert "execute" in rendered


def test_render_html_format(profile):
    reporter = QueryReporter(fmt="html", analyze=False)
    report = reporter.generate(profile)
    rendered = report.render()
    assert "<" in rendered


def test_to_json_is_string(reporter, profile):
    report = reporter.generate(profile)
    assert isinstance(report.to_json(), str)


def test_to_csv_is_string(reporter, profile):
    report = reporter.generate(profile)
    assert isinstance(report.to_csv(), str)


def test_report_repr(reporter, profile):
    report = reporter.generate(profile)
    r = repr(report)
    assert "Report" in r
    assert "SELECT * FROM orders" in r


def test_invalid_fmt_raises():
    with pytest.raises(ValueError, match="Unsupported format"):
        QueryReporter(fmt="xml")


def test_invalid_threshold_raises():
    with pytest.raises(ValueError, match="threshold"):
        QueryReporter(threshold=1.5)


def test_no_analysis_on_error_profile(reporter):
    error_profile = ProfileResult(
        query="BAD SQL", stages=[], error="syntax error"
    )
    report = reporter.generate(error_profile)
    assert report.analysis is None
