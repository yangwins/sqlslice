"""Tests for sqlslice.cli_differ module."""

import pytest
from unittest.mock import MagicMock, patch, call

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.differ import ProfileDiffer
from sqlslice.cli_differ import run_differ_session, _build_parser


SQL = "SELECT 1"


def _make_result(error=None):
    stages = [Stage("parse", 0.05), Stage("execute", 0.3), Stage("fetch", 0.1)]
    return ProfileResult(query=SQL, stages=stages, error=error)


@pytest.fixture
def mock_profiler():
    p = MagicMock()
    p.profile.return_value = _make_result()
    return p


def test_run_differ_session_calls_profiler_n_times(mock_profiler, capsys):
    run_differ_session(SQL, runs=3, profiler=mock_profiler)
    assert mock_profiler.profile.call_count == 3


def test_run_differ_session_prints_summary(mock_profiler, capsys):
    run_differ_session(SQL, runs=2, profiler=mock_profiler)
    out = capsys.readouterr().out
    assert SQL in out


def test_run_differ_session_on_result_callback(mock_profiler):
    collected = []
    run_differ_session(SQL, runs=3, profiler=mock_profiler, on_result=lambda i, r: collected.append(i))
    assert collected == [1, 2, 3]


def test_run_differ_session_invalid_runs(mock_profiler):
    with pytest.raises(ValueError, match="runs must be"):
        run_differ_session(SQL, runs=0, profiler=mock_profiler)


def test_run_differ_session_with_error_result(capsys):
    p = MagicMock()
    p.profile.return_value = _make_result(error="timeout")
    run_differ_session(SQL, runs=2, profiler=p)
    out = capsys.readouterr().out
    assert "Errors" in out


def test_build_parser_defaults():
    parser = _build_parser()
    args = parser.parse_args(["SELECT 1"])
    assert args.runs == 5
    assert args.delay == 0.0
    assert args.dsn is None


def test_build_parser_custom_runs():
    parser = _build_parser()
    args = parser.parse_args(["SELECT 1", "--runs", "10"])
    assert args.runs == 10


def test_build_parser_custom_delay():
    parser = _build_parser()
    args = parser.parse_args(["SELECT 1", "--delay", "1.5"])
    assert args.delay == pytest.approx(1.5)


def test_run_differ_session_delay_called(mock_profiler):
    with patch("sqlslice.cli_differ.time.sleep") as mock_sleep:
        run_differ_session(SQL, runs=3, profiler=mock_profiler, delay=0.5)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(0.5)


def test_run_differ_session_no_delay_not_called(mock_profiler):
    with patch("sqlslice.cli_differ.time.sleep") as mock_sleep:
        run_differ_session(SQL, runs=3, profiler=mock_profiler, delay=0.0)
        mock_sleep.assert_not_called()
