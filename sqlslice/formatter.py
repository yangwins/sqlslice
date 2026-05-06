"""Formatters for rendering ProfileResult reports as text or HTML."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlslice.profiler import ProfileResult


class TextFormatter:
    """Render a ProfileResult as a plain-text table."""

    HEADER = "{:<30} {:>12} {:>8}"
    ROW = "{:<30} {:>12.4f} {:>7.1f}%"
    DIVIDER_CHAR = "-"
    WIDTH = 54

    def format(self, result: "ProfileResult") -> str:
        lines: list[str] = []
        lines.append(f"Query: {result.query}")
        lines.append(self.DIVIDER_CHAR * self.WIDTH)
        lines.append(self.HEADER.format("Stage", "Duration (s)", "Share"))
        lines.append(self.DIVIDER_CHAR * self.WIDTH)

        total = result.total_duration
        for stage in result.stages:
            share = (stage.duration / total * 100) if total > 0 else 0.0
            lines.append(self.ROW.format(stage.name[:30], stage.duration, share))
            if stage.error:
                lines.append(f"  ! Error: {stage.error}")

        lines.append(self.DIVIDER_CHAR * self.WIDTH)
        lines.append(f"Total: {total:.4f}s")
        return "\n".join(lines)


class HTMLFormatter:
    """Render a ProfileResult as a simple HTML table."""

    def format(self, result: "ProfileResult") -> str:
        total = result.total_duration
        rows: list[str] = []
        for stage in result.stages:
            share = (stage.duration / total * 100) if total > 0 else 0.0
            error_cell = f"<td class='error'>{stage.error}</td>" if stage.error else "<td></td>"
            rows.append(
                f"<tr><td>{stage.name}</td>"
                f"<td>{stage.duration:.4f}</td>"
                f"<td>{share:.1f}%</td>"
                f"{error_cell}</tr>"
            )

        rows_html = "\n".join(rows)
        return (
            f"<table class='sqlslice-report'>"
            f"<caption>Query: {result.query}</caption>"
            f"<thead><tr>"
            f"<th>Stage</th><th>Duration (s)</th><th>Share</th><th>Error</th>"
            f"</tr></thead>"
            f"<tbody>{rows_html}</tbody>"
            f"<tfoot><tr><td colspan='4'>Total: {total:.4f}s</td></tr></tfoot>"
            f"</table>"
        )


def get_formatter(fmt: str = "text") -> TextFormatter | HTMLFormatter:
    """Return a formatter instance by name ('text' or 'html')."""
    if fmt == "html":
        return HTMLFormatter()
    if fmt == "text":
        return TextFormatter()
    raise ValueError(f"Unknown formatter: {fmt!r}. Choose 'text' or 'html'.")
