from collections import Counter
from dataclasses import dataclass
from typing import Any, cast

import decouple
import disnake
import pydantic
from disnake.ext import commands

import faceit
from faceit.constants import FACEIT_PRIMARY_COLOR
from faceit.models.players import GameInfo, MatchResult, Player


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


async def analyze_cs2_recent_matches(
    data: faceit.AsyncDataResource,
    player_id: str,
    *,
    limit: int,
) -> MatchAnalysis | None:
    matches = await data.players.matches_stats(
        player_id, faceit.GameID.CS2, limit=limit
    )
    if not matches:
        return None

    total = len(matches)
    wins_page = matches.filter(lambda m: m.result is MatchResult.WIN)
    wins = len(wins_page)

    avg_kd = sum(m.kd_ratio for m in matches) / total
    avg_adr = sum(m.adr for m in matches) / total
    avg_hs = sum(m.headshots_percentage for m in matches) / total
    total_kills = sum(m.kills for m in matches)
    total_deaths = sum(m.deaths for m in matches)
    total_assists = sum(m.assists for m in matches)

    map_counts = Counter(m.map for m in matches)
    map_wins = Counter(m.map for m in wins_page)
    most_played_map, most_played_count = map_counts.most_common(1)[0]

    best_map = max(
        (m for m, c in map_counts.items() if c >= 2),
        key=lambda m: map_wins.get(m, 0) / map_counts[m],
        default=None,
    )
    best_map_wr = (
        map_wins.get(best_map, 0) / map_counts[best_map] * 100
        if best_map is not None
        else None
    )

    return MatchAnalysis(
        total=total,
        wins=wins,
        win_rate=wins / total * 100,
        avg_kd=avg_kd,
        avg_adr=avg_adr,
        avg_hs_pct=avg_hs,
        total_kills=total_kills,
        total_deaths=total_deaths,
        total_assists=total_assists,
        most_played_map=most_played_map,
        most_played_map_count=most_played_count,
        best_map=best_map,
        best_map_win_rate=best_map_wr,
    )


class StatsCommand(commands.Cog):
    def __init__(
        self,
        bot: commands.InteractionBot,
        faceit_data: faceit.AsyncDataResource,
    ) -> None:
        self.bot = bot
        self.faceit_data = faceit_data

    async def cog_slash_command_error(  # noqa: PLR6301
        self,
        inter: disnake.CommandInteraction[Any],
        error: Exception,
    ) -> None:
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        player_name = inter.filled_options.get("player_name", "<unknown>")
        match error:
            case pydantic.ValidationError():
                await inter.edit_original_response(
                    f"⚠️ We couldn't process the profile for `{player_name}`. "
                    "Please check if the nickname is entered correctly."
                )
            case faceit.NotFoundError():
                await inter.edit_original_response(
                    f"❌ Player `{player_name}` not found."
                )
            case faceit.APIError():
                await inter.edit_original_response(
                    f"⚠️ API Error (`{error.status_code}`): {error.message}"
                )
            case _:
                await inter.edit_original_response(
                    "💥 An unexpected error occurred. Please try again later."
                )

    @commands.slash_command(
        name="stats",
        description="Show detailed FACEIT CS2 player statistics",
    )
    async def stats(
        self,
        inter: disnake.CommandInteraction[Any],
        player_name: str = commands.Param(
            description="FACEIT player nickname",
        ),
    ) -> disnake.Message | None:
        context = await self._prepare_player_context(inter, player_name)
        if context is None:
            return None
        player, cs2_stats, embed = context

        player_stats = await self.faceit_data.players.stats(
            player.id, faceit.GameID.CS2
        )

        embed.title = f"{player.nickname}'s Statistics"
        embed.add_field("🎮 Level", f"**{int(cs2_stats.level)} LVL**")
        embed.add_field("📈 ELO", f"**{cs2_stats.elo}**")
        embed.add_field("📊 K/D", f"**{player_stats.lifetime.average_kd_ratio}**")
        embed.add_field("🏆 Win Rate", f"**{player_stats.lifetime.win_rate}%**")
        embed.add_field("⚔️ Matches", f"**{player_stats.lifetime.matches}**")
        if player_stats.lifetime.recent_results:
            results = " ".join(
                "✅" if result is MatchResult.WIN else "❌"
                for result in player_stats.lifetime.recent_results
            )
            embed.add_field("🕊️ Recent Results", results, inline=False)

        return await inter.edit_original_response(embed=embed)

    @commands.slash_command(
        name="recent",
        description="Show CS2 performance summary for recent matches",
    )
    async def recent(
        self,
        inter: disnake.CommandInteraction[Any],
        player_name: str = commands.Param(
            description="FACEIT player nickname",
        ),
        matches: int = commands.Param(
            20,
            description="Number of recent matches to analyse (1-100)",
            min_value=1,
            max_value=100,
        ),
    ) -> disnake.Message | None:
        context = await self._prepare_player_context(inter, player_name)
        if context is None:
            return None
        player, _, embed = context

        analysis = await analyze_cs2_recent_matches(
            self.faceit_data, str(player.id), limit=matches
        )
        if analysis is None:
            return await inter.edit_original_response(
                f"📭 No matches found for `{player.nickname}`."
            )

        embed.title = f"{player.nickname} — Last {analysis.total} matches"
        embed.add_field(
            "🏆 W / L",
            f"**{analysis.wins}W - {analysis.losses}L** ({analysis.win_rate:.0f}%)",
            inline=True,
        )
        embed.add_field("📊 Avg K/D", f"**{analysis.avg_kd:.2f}**")
        embed.add_field("💥 Avg ADR", f"**{analysis.avg_adr:.1f}**")
        embed.add_field("🎯 Avg HS%", f"**{analysis.avg_hs_pct:.1f}%**")
        embed.add_field(
            "⚔️ K / D / A",
            f"**{analysis.total_kills} / {analysis.total_deaths} / {analysis.total_assists}**",
        )
        embed.add_field(
            "🗺️ Most played",
            f"**{analysis.most_played_map}** ({analysis.most_played_map_count} games)",
        )
        if analysis.best_map is not None:
            embed.add_field(
                "⭐ Best map",
                f"**{analysis.best_map}** ({analysis.best_map_win_rate:.0f}% WR)",
            )

        return await inter.edit_original_response(embed=embed)

    async def _prepare_player_context(
        self, inter: disnake.CommandInteraction[Any], player_name: str
    ) -> tuple[Player, GameInfo, disnake.Embed] | None:
        await inter.response.defer()

        player = await self.faceit_data.players.get(player_name)

        cs2_stats = player.games.get(faceit.GameID.CS2)
        if cs2_stats is None:
            await inter.edit_original_response(
                f"🔎 Player `{player.nickname}` found, but they don't have CS2 linked."
            )
            return None

        embed = disnake.Embed(url=player.faceit_url, color=FACEIT_PRIMARY_COLOR)
        if player.avatar:
            embed.set_thumbnail(url=player.avatar)
        embed.set_footer(text="Powered by faceit-python")

        return player, cs2_stats, embed


async def main() -> None:
    bot = commands.InteractionBot()
    bot_token = cast("str", decouple.config("DISCORD_BOT_TOKEN"))
    async with faceit.AsyncDataResource() as data:
        bot.add_cog(StatsCommand(bot, data))
        await bot.start(bot_token)


if __name__ == "__main__":
    import asyncio
    from contextlib import suppress

    with suppress(KeyboardInterrupt, asyncio.CancelledError):
        asyncio.run(main())
