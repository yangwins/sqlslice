"""Tests for sqlslice.annotator."""
import pytest
from sqlslice.profiler import Stage, ProfileResult
from sqlslice.annotator import AnnotatedStage, AnnotationReport, QueryAnnotator


@pytest.fixture()
def stages():
    return [
        Stage(name="parse", duration_ms=5.0),
        Stage(name="plan", duration_ms=12.0),
        Stage(name="execute", duration_ms=80.0),
    ]


@pytest.fixture()
def result(stages):
    return ProfileResult(query="SELECT 1", stages=stages, total_duration_ms=97.0)


@pytest.fixture()
def annotator():
    ann = QueryAnnotator()
    ann.add_note("parse", "tokenisation step")
    ann.add_note("execute", "full table scan detected")
    return ann


def test_annotate_returns_annotation_report(annotator, result):
    report = annotator.annotate(result)
    assert isinstance(report, AnnotationReport)


def test_annotation_report_query_preserved(annotator, result):
    report = annotator.annotate(result)
    assert report.query == "SELECT 1"


def test_annotated_count_matches_registered_notes(annotator, result):
    report = annotator.annotate(result)
    assert report.annotated_count == 2


def test_unannotated_stage_absent(annotator, result):
    report = annotator.annotate(result)
    assert report.get("plan") is None


def test_annotated_stage_note_correct(annotator, result):
    report = annotator.annotate(result)
    ann = report.get("execute")
    assert ann is not None
    assert ann.note == "full table scan detected"


def test_annotated_stage_carries_original_stage(annotator, result):
    report = annotator.annotate(result)
    ann = report.get("parse")
    assert ann.stage.duration_ms == 5.0


def test_no_notes_produces_empty_report(result):
    empty_annotator = QueryAnnotator()
    report = empty_annotator.annotate(result)
    assert report.annotated_count == 0


def test_summary_contains_query(annotator, result):
    summary = annotator.annotate(result).summary()
    assert "SELECT 1" in summary


def test_summary_contains_note(annotator, result):
    summary = annotator.annotate(result).summary()
    assert "full table scan detected" in summary


def test_summary_empty_annotations_message(result):
    summary = QueryAnnotator().annotate(result).summary()
    assert "no annotations" in summary


def test_remove_note_reduces_count(annotator, result):
    annotator.remove_note("execute")
    report = annotator.annotate(result)
    assert report.annotated_count == 1


def test_remove_nonexistent_note_is_noop(annotator):
    annotator.remove_note("nonexistent")  # should not raise


def test_add_empty_stage_name_raises():
    with pytest.raises(ValueError, match="stage_name"):
        QueryAnnotator().add_note("", "some note")


def test_add_empty_note_raises():
    with pytest.raises(ValueError, match="note"):
        QueryAnnotator().add_note("parse", "")


def test_annotated_stage_repr():
    stage = Stage(name="plan", duration_ms=10.0)
    ann = AnnotatedStage(stage=stage, note="hi")
    assert "plan" in repr(ann)
    assert "hi" in repr(ann)


def test_annotation_report_repr(annotator, result):
    report = annotator.annotate(result)
    assert "AnnotationReport" in repr(report)
    assert "annotated_count=2" in repr(report)
