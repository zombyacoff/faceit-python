from contextlib import suppress
from dataclasses import dataclass
from typing import Any, cast

import decouple
import disnake
import pydantic
from disnake.ext import commands

import faceit
import faceit.exceptions
from faceit.models.players import MatchResult


@dataclass(repr=False, eq=False)
class StatsCommand(commands.Cog):
    bot: commands.InteractionBot
    faceit_data: faceit.AsyncDataResource

    async def cog_slash_command_error(  # noqa: PLR6301
        self,
        inter: disnake.ApplicationCommandInteraction[Any],
        error: Exception,
    ) -> None:
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        player_name = inter.filled_options.get("player_name", "")

        match error:
            case pydantic.ValidationError():
                await inter.edit_original_response(
                    f"⚠️ We couldn't process the profile for `{player_name}`. "
                    "Please check if the nickname is entered correctly."
                )
            case faceit.exceptions.NotFoundError():
                await inter.edit_original_response(
                    f"❌ Player `{player_name}` not found."
                )
            case faceit.exceptions.APIError():
                await inter.edit_original_response(
                    f"⚠️ API Error [{error.status_code}]: {error.message}"
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
        inter: disnake.ApplicationCommandInteraction[Any],
        player_name: str = commands.Param(
            description="FACEIT player nickname",
        ),
    ) -> disnake.Message:
        await inter.response.defer()

        player = await self.faceit_data.players.get(player_name)

        cs2_game = player.games.get(faceit.GameID.CS2)
        if cs2_game is None:
            return await inter.edit_original_response(
                f"🔎 Player **{player.nickname}** found, "
                "but they don't have CS2 linked."
            )

        player_stats = await self.faceit_data.players.stats(
            player.id, faceit.GameID.CS2
        )

        embed = disnake.Embed(
            title=f"{player.nickname}'s Statistics",
            url=player.faceit_url,
            color=faceit.constants.FACEIT_COLOR,
        )

        if player.avatar:
            embed.set_thumbnail(url=player.avatar)

        embed.add_field("🎮 Level", f"**{int(cs2_game.level)} LVL**", inline=True)
        embed.add_field("📈 ELO", f"**{cs2_game.elo}**", inline=True)
        embed.add_field(
            "📊 K/D",
            f"**{player_stats.lifetime.average_kd_ratio}**",
            inline=True,
        )
        embed.add_field(
            "🏆 Win Rate",
            f"**{player_stats.lifetime.win_rate}%**",
            inline=True,
        )
        embed.add_field(
            "⚔️ Matches",
            f"**{player_stats.lifetime.matches}**",
            inline=True,
        )

        if player_stats.lifetime.recent_results:
            embed.add_field(
                "Recent Results",
                " ".join(
                    "✅" if result is MatchResult.WIN else "❌"
                    for result in player_stats.lifetime.recent_results
                ),
                inline=False,
            )

        embed.set_footer(text="Powered by faceit-python")
        return await inter.edit_original_response(embed=embed)


async def main() -> None:
    bot = commands.InteractionBot()
    bot_token = cast(
        "str",
        decouple.config(  # Included with `faceit[env]` installation
            "DISCORD_BOT_TOKEN"
        ),
    )
    async with (
        # NOTE: Ensure the `FACEIT_API_KEY` is set in your environment variables
        # (Requires `faceit[env]` to be installed)
        faceit.AsyncDataResource()  # or use faceit.AsyncDataResource("YOUR_FACEIT_API_KEY")
    ) as data:
        bot.add_cog(StatsCommand(bot, data))
        await bot.start(bot_token)


if __name__ == "__main__":
    import asyncio

    with suppress(KeyboardInterrupt, asyncio.CancelledError):  # CTRL+C
        asyncio.run(main())
