from contextlib import suppress

import decouple
import disnake
import pydantic
from disnake.ext import commands

import faceit


# For IDE auto-completion
class FaceitDiscordBot(commands.InteractionBot):
    def setup_faceit(self, data: faceit.AsyncDataResource, /) -> None:
        self.faceit_data = data


bot = FaceitDiscordBot()


@bot.slash_command(
    name="stats",
    description="Show detailed FACEIT CS2 player statistics",
)
async def stats(
    inter: disnake.ApplicationCommandInteraction,
    player_name: str = commands.Param(
        description="FACEIT player nickname",
    ),
) -> None:
    await inter.response.defer()

    try:
        player = await bot.faceit_data.players.get(player_name)

        cs2_game = player.games.get(faceit.GameID.CS2)
        if cs2_game is None:
            return await inter.edit_original_response(
                f"🔎 Player **{player.nickname}** found, but they don't have CS2 linked."
            )

        player_stats = await bot.faceit_data.players.stats(player.id, faceit.GameID.CS2)

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

        recent = " ".join(
            "✅" if m == 1 else "❌" for m in player_stats.lifetime.recent_results
        )
        if recent:
            embed.add_field("Recent Results", recent, inline=False)

        embed.set_footer(text="FACEIT Stats Bot • CS2 Edition")
        await inter.edit_original_response(embed=embed)

    except faceit.exceptions.NotFoundError:
        await inter.edit_original_response(f"❌ Player **{player_name}** not found.")

    except faceit.APIError as e:
        await inter.edit_original_response(f"⚠️ API Error: {e}")

    except pydantic.ValidationError as e:
        await inter.edit_original_response(
            f"⚠️ We couldn't process the profile for **{player_name}**. "
            "Please check if the nickname is entered correctly."
        )

    except Exception as e:
        await inter.edit_original_response(
            "💥 An unexpected error occurred. Please try again later."
        )


async def main() -> None:
    async with (
        # NOTE: Ensure the `FACEIT_API_KEY` is set in your environment variables.
        # (Requires `faceit[env]` to be installed)
        faceit.AsyncDataResource()  # Or use faceit.AsyncDataResource("YOUR_FACEIT_API_KEY")
    ) as data:
        bot.setup_faceit(data)
        await bot.start(
            decouple.config(  # Included with `faceit[env]` installation
                "DISCORD_BOT_TOKEN"
            )
        )


if __name__ == "__main__":
    import asyncio

    with suppress(KeyboardInterrupt, asyncio.CancelledError):  # CTRL+C
        asyncio.run(main())
