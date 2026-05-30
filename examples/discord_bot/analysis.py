from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from faceit.models.players import MatchResult

if TYPE_CHECKING:
    from faceit.models import CS2MatchPlayerStats, ItemPage


@dataclass(frozen=True, kw_only=True, slots=True)
class MatchAnalysis:
    total: int
    wins: int
    win_rate: float
    avg_kd: float
    avg_adr: float
    avg_hs_pct: float
    total_kills: int
    total_deaths: int
    total_assists: int
    most_played_map: str
    most_played_map_count: int
    best_map: str | None
    best_map_win_rate: float | None

    @property
    def losses(self) -> int:
        return self.total - self.wins


def analyze_cs2_recent_matches(
    matches: ItemPage[CS2MatchPlayerStats], /
) -> MatchAnalysis:
    total = len(matches)

    total_kills = 0
    total_deaths = 0
    total_assists = 0
    sum_kd = 0.0
    sum_adr = 0.0
    sum_hs = 0.0
    wins = 0

    map_counts: Counter[str] = Counter()
    map_wins: Counter[str] = Counter()

    for m in matches:
        total_kills += m.kills
        total_deaths += m.deaths
        total_assists += m.assists
        sum_kd += m.kd_ratio
        sum_adr += m.adr
        sum_hs += m.headshots_percentage

        map_counts[m.map] += 1
        if m.result is MatchResult.WIN:
            wins += 1
            map_wins[m.map] += 1

    most_played_map, most_played_count = map_counts.most_common(1)[0]
    best_map = max(
        (m for m, c in map_counts.items() if c >= 2),
        key=lambda m: map_wins[m] / map_counts[m],
        default=None,
    )
    best_map_wr = (
        None if best_map is None else (map_wins[best_map] / map_counts[best_map] * 100)
    )

    return MatchAnalysis(
        total=total,
        wins=wins,
        win_rate=wins / total * 100,
        avg_kd=sum_kd / total,
        avg_adr=sum_adr / total,
        avg_hs_pct=sum_hs / total,
        total_kills=total_kills,
        total_deaths=total_deaths,
        total_assists=total_assists,
        most_played_map=most_played_map,
        most_played_map_count=most_played_count,
        best_map=best_map,
        best_map_win_rate=best_map_wr,
    )
