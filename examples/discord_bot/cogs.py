from __future__ import annotations

from typing import TYPE_CHECKING, Any

import disnake
import pydantic
from disnake.ext import commands

import faceit
from faceit.constants import FACEIT_PRIMARY_COLOR
from faceit.models.players import GameInfo, MatchResult

from .analysis import analyze_cs2_recent_matches

if TYPE_CHECKING:
    from faceit.models import Player

    from .bot import FaceitBot


class FaceitCog(commands.Cog):
    def __init__(self, /, bot: FaceitBot) -> None:
        self.bot = bot

    @property
    def faceit_data(self) -> faceit.AsyncDataResource:
        if self.bot.data is not None:
            return self.bot.data
        msg = "FACEIT API data resource is not initialized."
        raise RuntimeError(msg)


class StatsCommand(FaceitCog):
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
                message = (
                    f"⚠️ We couldn't process the profile for `{player_name}`. "
                    "Please check if the nickname is entered correctly."
                )
            case faceit.NotFoundError():
                message = f"❌ Player `{player_name}` not found."
            case faceit.APIError():
                message = f"⚠️ API Error (`{error.status_code}`): {error.message}"
            case _:
                message = "💥 An unexpected error occurred. Please try again later."

        if inter.response.is_done():
            await inter.edit_original_response(message)
        else:
            await inter.response.send_message(message, ephemeral=True)

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
            default=20,
            description="Number of recent matches to analyse (1-100)",
            min_value=1,
            max_value=100,
        ),
    ) -> disnake.Message | None:
        context = await self._prepare_player_context(inter, player_name)
        if context is None:
            return None
        player, _, embed = context

        matches_stats = await self.faceit_data.players.matches_stats(
            player.id, faceit.GameID.CS2, limit=matches
        )
        if not matches_stats:
            return await inter.edit_original_response(
                f"📭 No matches found for `{player.nickname}`."
            )
        analysis = analyze_cs2_recent_matches(matches_stats)

        embed.title = f"{player.nickname} — Last {analysis.total} matches"
        embed.add_field(
            "🏆 W / L",
            f"**{analysis.wins}W - {analysis.losses}L** ({analysis.win_rate:.0f}%)",
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
