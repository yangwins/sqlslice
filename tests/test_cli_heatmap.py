"""Tests for sqlslice.cli_heatmap."""
import io
import pytest
from unittest.mock import MagicMock

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.heatmap import QueryHeatmap
from sqlslice.cli_heatmap import _build_parser, run_heatmap_session


def _make_result(durations: dict, query: str = "SELECT 1") -> ProfileResult:
    stages = [Stage(name=k, duration_ms=v) for k, v in durations.items()]
    return ProfileResult(query=query, stages=stages, total_duration_ms=sum(durations.values()))


@pytest.fixture
def mock_profiler():
    profiler = MagicMock()
    profiler.profile.side_effect = [
        _make_result({"parse": 5.0, "execute": 20.0}),
        _make_result({"parse": 6.0, "execute": 25.0}),
        _make_result({"parse": 4.0, "execute": 18.0}),
    ]
    return profiler


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def test_parser_defaults():
    parser = _build_parser()
    args = parser.parse_args(["SELECT 1"])
    assert args.runs == 5
    assert args.quiet is False
    assert args.dsn is None


def test_parser_custom_runs():
    parser = _build_parser()
    args = parser.parse_args(["SELECT 1", "--runs", "3"])
    assert args.runs == 3


def test_parser_quiet_flag():
    parser = _build_parser()
    args = parser.parse_args(["SELECT 1", "--quiet"])
    assert args.quiet is True


# ---------------------------------------------------------------------------
# run_heatmap_session
# ---------------------------------------------------------------------------

def test_run_heatmap_session_calls_profiler_n_times(mock_profiler):
    out = io.StringIO()
    run_heatmap_session("SELECT 1", runs=3, profiler=mock_profiler, out=out)
    assert mock_profiler.profile.call_count == 3


def test_run_heatmap_session_returns_heatmap(mock_profiler):
    out = io.StringIO()
    result = run_heatmap_session("SELECT 1", runs=3, profiler=mock_profiler, out=out)
    assert isinstance(result, QueryHeatmap)


def test_run_heatmap_session_output_contains_summary(mock_profiler):
    out = io.StringIO()
    run_heatmap_session("SELECT 1", runs=3, profiler=mock_profiler, out=out)
    output = out.getvalue()
    assert "SELECT 1" in output


def test_run_heatmap_session_quiet_suppresses_run_lines(mock_profiler):
    out = io.StringIO()
    run_heatmap_session("SELECT 1", runs=3, profiler=mock_profiler, quiet=True, out=out)
    output = out.getvalue()
    assert "run 1/3" not in output


def test_run_heatmap_session_not_quiet_shows_run_lines(mock_profiler):
    out = io.StringIO()
    run_heatmap_session("SELECT 1", runs=3, profiler=mock_profiler, quiet=False, out=out)
    output = out.getvalue()
    assert "run 1/3" in output


def test_run_heatmap_session_invalid_runs_raises(mock_profiler):
    with pytest.raises(ValueError, match="runs must be >= 1"):
        run_heatmap_session("SELECT 1", runs=0, profiler=mock_profiler)


def test_run_heatmap_session_output_contains_stage_name(mock_profiler):
    out = io.StringIO()
    run_heatmap_session("SELECT 1", runs=3, profiler=mock_profiler, out=out)
    output = out.getvalue()
    assert "execute" in output
