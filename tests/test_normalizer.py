"""Tests for sqlslice.normalizer."""
import pytest
from sqlslice.normalizer import NormalizedQuery, QueryNormalizer


@pytest.fixture
def normalizer():
    return QueryNormalizer()


# --- NormalizedQuery ---

def test_normalized_query_fingerprint_lowercased(normalizer):
    nq = normalizer.normalize("SELECT id FROM users WHERE id = ?")
    assert nq.fingerprint() == nq.fingerprint().lower()


def test_normalized_query_tokens_not_empty(normalizer):
    nq = normalizer.normalize("SELECT 1")
    assert len(nq.tokens) > 0


def test_normalized_query_original_preserved(normalizer):
    sql = "  select id from users  "
    nq = normalizer.normalize(sql)
    assert nq.original == sql.strip()


# --- QueryNormalizer.normalize ---

def test_normalize_raises_on_non_string(normalizer):
    with pytest.raises(TypeError):
        normalizer.normalize(123)


def test_normalize_raises_on_empty_string(normalizer):
    with pytest.raises(ValueError):
        normalizer.normalize("   ")


def test_normalize_replaces_string_literals(normalizer):
    nq = normalizer.normalize("SELECT * FROM t WHERE name = 'Alice'")
    assert "'Alice'" not in nq.normalized
    assert "'?'" in nq.normalized


def test_normalize_replaces_numeric_literals(normalizer):
    nq = normalizer.normalize("SELECT * FROM t WHERE id = 42")
    assert '42' not in nq.normalized
    assert '?' in nq.normalized


def test_normalize_uppercases_keywords(normalizer):
    nq = normalizer.normalize("select id from users")
    assert 'SELECT' in nq.normalized
    assert 'FROM' in nq.normalized


def test_normalize_collapses_whitespace(normalizer):
    nq = normalizer.normalize("SELECT   id   FROM   users")
    assert '  ' not in nq.normalized


def test_normalize_returns_normalized_query_instance(normalizer):
    result = normalizer.normalize("SELECT 1")
    assert isinstance(result, NormalizedQuery)


# --- QueryNormalizer.are_equivalent ---

def test_are_equivalent_same_structure_different_literals(normalizer):
    a = "SELECT * FROM users WHERE id = 1"
    b = "SELECT * FROM users WHERE id = 99"
    assert normalizer.are_equivalent(a, b)


def test_are_equivalent_different_structure(normalizer):
    a = "SELECT id FROM users"
    b = "SELECT name FROM orders"
    assert not normalizer.are_equivalent(a, b)


def test_are_equivalent_whitespace_insensitive(normalizer):
    a = "SELECT id FROM users"
    b = "SELECT  id  FROM  users"
    assert normalizer.are_equivalent(a, b)


def test_are_equivalent_case_insensitive_keywords(normalizer):
    a = "select id from users"
    b = "SELECT id FROM users"
    assert normalizer.are_equivalent(a, b)
