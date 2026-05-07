"""Reporter module: combines profiling, analysis, and formatting into a single report."""

from dataclasses import dataclass, field
from typing import Optional

from sqlslice.profiler import ProfileResult
from sqlslice.analyzer import AnalysisReport, QueryAnalyzer
from sqlslice.formatter import get_formatter
from sqlslice.export import to_json, to_csv


@dataclass
class Report:
    """Unified report combining profiling results and analysis."""

    profile: ProfileResult
    analysis: Optional[AnalysisReport] = None
    fmt: str = "text"

    def render(self) -> str:
        """Render the profile result using the configured formatter."""
        formatter = get_formatter(self.fmt)
        output = formatter.format(self.profile)
        if self.analysis:
            output += "\n" + self.analysis.summary()
        return output

    def to_json(self) -> str:
        """Export the profile result as JSON."""
        return to_json(self.profile)

    def to_csv(self) -> str:
        """Export the profile result as CSV."""
        return to_csv(self.profile)

    def __repr__(self) -> str:
        return (
            f"Report(query={self.profile.query!r}, "
            f"stages={len(self.profile.stages)}, "
            f"fmt={self.fmt!r})"
        )


class QueryReporter:
    """Builds a unified Report from a ProfileResult with optional analysis."""

    def __init__(self, fmt: str = "text", threshold: float = 0.2, analyze: bool = True):
        if fmt not in ("text", "html"):
            raise ValueError(f"Unsupported format: {fmt!r}. Use 'text' or 'html'.")
        if not (0.0 < threshold < 1.0):
            raise ValueError("threshold must be between 0 and 1 (exclusive).")
        self.fmt = fmt
        self.threshold = threshold
        self.analyze = analyze

    def generate(self, profile: ProfileResult) -> Report:
        """Generate a Report from a ProfileResult."""
        analysis = None
        if self.analyze and not profile.error:
            analyzer = QueryAnalyzer(threshold=self.threshold)
            analysis = analyzer.analyze(profile)
        return Report(profile=profile, analysis=analysis, fmt=self.fmt)
