"""Stage ranker: sorts and ranks stages across a ProfileResult by duration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class RankedStage:
    """A stage decorated with its rank (1 = slowest)."""

    rank: int
    stage: Stage
    pct_of_total: float  # 0-100

    def __repr__(self) -> str:
        return (
            f"RankedStage(rank={self.rank}, name={self.stage.name!r}, "
            f"duration_ms={self.stage.duration_ms:.3f}, "
            f"pct_of_total={self.pct_of_total:.1f}%)"
        )


@dataclass
class RankReport:
    """Full ranking report for a single ProfileResult."""

    query: str
    ranked_stages: List[RankedStage]

    @property
    def slowest(self) -> RankedStage | None:
        return self.ranked_stages[0] if self.ranked_stages else None

    @property
    def fastest(self) -> RankedStage | None:
        return self.ranked_stages[-1] if self.ranked_stages else None

    def summary(self) -> str:
        lines = [f"Rank Report — {self.query}"]
        for rs in self.ranked_stages:
            lines.append(
                f"  #{rs.rank:>2}  {rs.stage.name:<30} "
                f"{rs.stage.duration_ms:>10.3f} ms  "
                f"({rs.pct_of_total:>5.1f}%)"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"RankReport(query={self.query!r}, stages={len(self.ranked_stages)})"


class StageRanker:
    """Ranks stages within a ProfileResult by descending duration."""

    def rank(self, result: ProfileResult) -> RankReport:
        """Return a RankReport with stages ordered slowest-first."""
        successful = [
            s for s in result.stages if s.error is None
        ]
        if not successful:
            return RankReport(query=result.query, ranked_stages=[])

        total_ms = sum(s.duration_ms for s in successful)
        sorted_stages = sorted(successful, key=lambda s: s.duration_ms, reverse=True)

        ranked: List[RankedStage] = []
        for idx, stage in enumerate(sorted_stages, start=1):
            pct = (stage.duration_ms / total_ms * 100) if total_ms > 0 else 0.0
            ranked.append(RankedStage(rank=idx, stage=stage, pct_of_total=pct))

        return RankReport(query=result.query, ranked_stages=ranked)
