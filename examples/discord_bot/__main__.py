from __future__ import annotations

import decouple

from .bot import FaceitBot
from .cogs import StatsCommand

bot = FaceitBot()
bot.add_cog(StatsCommand(bot))
bot.run(decouple.config("DISCORD_BOT_TOKEN"))
