"""Tests for sqlslice.formatter module."""

import pytest

from sqlslice.formatter import HTMLFormatter, TextFormatter, get_formatter
from sqlslice.profiler import ProfileResult, Stage


@pytest.fixture()
def simple_result() -> ProfileResult:
    stages = [
        Stage(name="parse", duration=0.01),
        Stage(name="plan", duration=0.05),
        Stage(name="execute", duration=0.44),
    ]
    return ProfileResult(query="SELECT 1", stages=stages)


@pytest.fixture()
def result_with_error() -> ProfileResult:
    stages = [
        Stage(name="parse", duration=0.01),
        Stage(name="execute", duration=0.0, error="timeout"),
    ]
    return ProfileResult(query="SELECT * FROM big", stages=stages)


# --- TextFormatter ---

def test_text_formatter_contains_query(simple_result):
    out = TextFormatter().format(simple_result)
    assert "SELECT 1" in out


def test_text_formatter_contains_stage_names(simple_result):
    out = TextFormatter().format(simple_result)
    for name in ("parse", "plan", "execute"):
        assert name in out


def test_text_formatter_total_line(simple_result):
    out = TextFormatter().format(simple_result)
    assert "Total:" in out
    assert "0.5000s" in out


def test_text_formatter_shows_error(result_with_error):
    out = TextFormatter().format(result_with_error)
    assert "timeout" in out
    assert "Error" in out


def test_text_formatter_share_sums_to_100(simple_result):
    """Shares printed in text output should add to ~100%."""
    out = TextFormatter().format(simple_result)
    import re
    shares = [float(m) for m in re.findall(r"(\d+\.\d+)%", out)]
    assert abs(sum(shares) - 100.0) < 0.2


# --- HTMLFormatter ---

def test_html_formatter_contains_table_tag(simple_result):
    out = HTMLFormatter().format(simple_result)
    assert "<table" in out and "</table>" in out


def test_html_formatter_contains_stage_names(simple_result):
    out = HTMLFormatter().format(simple_result)
    for name in ("parse", "plan", "execute"):
        assert name in out


def test_html_formatter_shows_error_cell(result_with_error):
    out = HTMLFormatter().format(result_with_error)
    assert "timeout" in out
    assert "error" in out


def test_html_formatter_total_in_footer(simple_result):
    out = HTMLFormatter().format(simple_result)
    assert "Total:" in out


# --- get_formatter factory ---

def test_get_formatter_text():
    assert isinstance(get_formatter("text"), TextFormatter)


def test_get_formatter_html():
    assert isinstance(get_formatter("html"), HTMLFormatter)


def test_get_formatter_default():
    assert isinstance(get_formatter(), TextFormatter)


def test_get_formatter_unknown():
    with pytest.raises(ValueError, match="Unknown formatter"):
        get_formatter("csv")
