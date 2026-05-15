"""Stage-level annotation support for ProfileResult objects."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from sqlslice.profiler import ProfileResult, Stage


@dataclass
class AnnotatedStage:
    """A stage decorated with a user-supplied note."""
    stage: Stage
    note: str

    def __repr__(self) -> str:
        return f"AnnotatedStage(name={self.stage.name!r}, note={self.note!r})"


@dataclass
class AnnotationReport:
    """Collection of annotated stages for a single ProfileResult."""
    query: str
    annotations: List[AnnotatedStage] = field(default_factory=list)

    @property
    def annotated_count(self) -> int:
        return len(self.annotations)

    def get(self, stage_name: str) -> Optional[AnnotatedStage]:
        """Return the AnnotatedStage for *stage_name*, or None."""
        for ann in self.annotations:
            if ann.stage.name == stage_name:
                return ann
        return None

    def summary(self) -> str:
        lines = [f"Query : {self.query}"]
        if not self.annotations:
            lines.append("  (no annotations)")
        else:
            for ann in self.annotations:
                lines.append(f"  [{ann.stage.name}] {ann.stage.duration_ms:.2f} ms — {ann.note}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"AnnotationReport(query={self.query!r}, annotated_count={self.annotated_count})"


class QueryAnnotator:
    """Attach text notes to individual stages of a ProfileResult."""

    def __init__(self) -> None:
        self._notes: Dict[str, str] = {}

    def add_note(self, stage_name: str, note: str) -> None:
        """Register *note* for any stage whose name matches *stage_name*."""
        if not stage_name:
            raise ValueError("stage_name must be a non-empty string")
        if not note:
            raise ValueError("note must be a non-empty string")
        self._notes[stage_name] = note

    def remove_note(self, stage_name: str) -> None:
        """Remove a previously registered note (no-op if absent)."""
        self._notes.pop(stage_name, None)

    def annotate(self, result: ProfileResult) -> AnnotationReport:
        """Return an AnnotationReport for *result* using registered notes."""
        annotations: List[AnnotatedStage] = []
        for stage in result.stages:
            if stage.name in self._notes:
                annotations.append(AnnotatedStage(stage=stage, note=self._notes[stage.name]))
        return AnnotationReport(query=result.query, annotations=annotations)
