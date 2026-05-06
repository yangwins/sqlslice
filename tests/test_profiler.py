"""Tests for sqlslice.profiler — QueryProfiler and ProfileResult."""

import sqlite3

import pytest

from sqlslice.profiler import ProfileResult, QueryProfiler, Stage


@pytest.fixture()
def conn():
    """In-memory SQLite connection with a small test table."""
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    c.executemany("INSERT INTO users VALUES (?, ?)", [(1, 'Alice'), (2, 'Bob')])
    c.commit()
    yield c
    c.close()


@pytest.fixture()
def profiler(conn):
    return QueryProfiler(conn)


# ---------------------------------------------------------------------------
# Stage dataclass
# ---------------------------------------------------------------------------

def test_stage_repr():
    s = Stage(name="execute", duration_ms=12.345)
    assert "execute" in repr(s)
    assert "12.345" in repr(s)


# ---------------------------------------------------------------------------
# ProfileResult.summary
# ---------------------------------------------------------------------------

def test_profile_result_summary_contains_query_and_total():
    result = ProfileResult(query="SELECT 1", stages=[], total_ms=5.0)
    summary = result.summary()
    assert "SELECT 1" in summary
    assert "5.000 ms" in summary


def test_profile_result_summary_shows_error():
    result = ProfileResult(query="BAD", total_ms=0.0, error="syntax error")
    assert "syntax error" in result.summary()


# ---------------------------------------------------------------------------
# QueryProfiler.profile — happy path
# ---------------------------------------------------------------------------

def test_profile_returns_three_stages(profiler):
    result = profiler.profile("SELECT * FROM users")
    assert result.error is None
    assert len(result.stages) == 3
    names = [s.name for s in result.stages]
    assert names == ["cursor_acquire", "execute", "fetchall"]


def test_profile_total_ms_equals_sum_of_stages(profiler):
    result = profiler.profile("SELECT * FROM users")
    assert result.total_ms == pytest.approx(
        sum(s.duration_ms for s in result.stages), rel=1e-6
    )


def test_profile_fetchall_row_count(profiler):
    result = profiler.profile("SELECT * FROM users")
    fetch_stage = next(s for s in result.stages if s.name == "fetchall")
    assert fetch_stage.metadata["row_count"] == 2


def test_profile_with_params(profiler):
    result = profiler.profile("SELECT * FROM users WHERE id = ?", params=(1,))
    assert result.error is None
    fetch_stage = next(s for s in result.stages if s.name == "fetchall")
    assert fetch_stage.metadata["row_count"] == 1


def test_profile_all_durations_non_negative(profiler):
    result = profiler.profile("SELECT 1")
    for stage in result.stages:
        assert stage.duration_ms >= 0


# ---------------------------------------------------------------------------
# QueryProfiler.profile — error path
# ---------------------------------------------------------------------------

def test_profile_bad_sql_sets_error(profiler):
    result = profiler.profile("SELECT * FROM nonexistent_table")
    assert result.error is not None
    assert "execution failed" in result.error
