"""Tests for sqlslice.truncator."""

import pytest

from sqlslice.truncator import QueryTruncator, TruncatedQuery, _DEFAULT_MAX_LENGTH


@pytest.fixture
def truncator() -> QueryTruncator:
    return QueryTruncator(max_length=40)


SHORT_QUERY = "SELECT 1"
LONG_QUERY = "SELECT id, name, email FROM users WHERE active = 1 AND deleted_at IS NULL ORDER BY name"


# --- construction ---

def test_default_max_length():
    t = QueryTruncator()
    assert t.max_length == _DEFAULT_MAX_LENGTH


def test_invalid_max_length_zero():
    with pytest.raises(ValueError, match="positive integer"):
        QueryTruncator(max_length=0)


def test_invalid_max_length_negative():
    with pytest.raises(ValueError, match="positive integer"):
        QueryTruncator(max_length=-5)


def test_invalid_max_length_non_int():
    with pytest.raises(ValueError):
        QueryTruncator(max_length=10.5)  # type: ignore[arg-type]


def test_max_length_too_small_for_ellipsis():
    with pytest.raises(ValueError, match="ellipsis"):
        QueryTruncator(max_length=2)


# --- short query (no truncation) ---

def test_short_query_not_truncated(truncator):
    result = truncator.truncate(SHORT_QUERY)
    assert isinstance(result, TruncatedQuery)
    assert result.was_truncated is False


def test_short_query_original_equals_truncated(truncator):
    result = truncator.truncate(SHORT_QUERY)
    assert result.truncated == SHORT_QUERY


def test_short_query_lengths_match(truncator):
    result = truncator.truncate(SHORT_QUERY)
    assert result.original_length == result.truncated_length == len(SHORT_QUERY)


# --- long query (truncation) ---

def test_long_query_is_truncated(truncator):
    result = truncator.truncate(LONG_QUERY)
    assert result.was_truncated is True


def test_long_query_truncated_length_within_max(truncator):
    result = truncator.truncate(LONG_QUERY)
    assert result.truncated_length <= truncator.max_length


def test_long_query_ends_with_ellipsis(truncator):
    result = truncator.truncate(LONG_QUERY)
    assert result.truncated.endswith("...")


def test_long_query_original_preserved(truncator):
    result = truncator.truncate(LONG_QUERY)
    assert result.original == LONG_QUERY


# --- custom placeholder ---

def test_custom_placeholder(truncator):
    result = truncator.truncate(LONG_QUERY, placeholder="[SNIP]")
    assert result.truncated.endswith("[SNIP]")


def test_custom_placeholder_length_respected(truncator):
    result = truncator.truncate(LONG_QUERY, placeholder="[SNIP]")
    assert result.truncated_length <= truncator.max_length


# --- type errors ---

def test_non_string_query_raises(truncator):
    with pytest.raises(TypeError, match="str"):
        truncator.truncate(12345)  # type: ignore[arg-type]


# --- truncate_many ---

def test_truncate_many_returns_list(truncator):
    results = truncator.truncate_many([SHORT_QUERY, LONG_QUERY])
    assert len(results) == 2
    assert all(isinstance(r, TruncatedQuery) for r in results)


def test_truncate_many_empty_list(truncator):
    assert truncator.truncate_many([]) == []


# --- repr ---

def test_repr_not_truncated(truncator):
    r = truncator.truncate(SHORT_QUERY)
    assert "TruncatedQuery" in repr(r)
    assert "*" not in repr(r)


def test_repr_truncated_has_asterisk(truncator):
    r = truncator.truncate(LONG_QUERY)
    assert "*" in repr(r)
