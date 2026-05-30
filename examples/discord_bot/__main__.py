from __future__ import annotations

import logging

import decouple

from .bot import FaceitBot
from .cogs import StatsCommand

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def main() -> None:
    if (token := decouple.config("DISCORD_BOT_TOKEN", default=None)) is None:
        logger.error("DISCORD_BOT_TOKEN not found in environment or .env file.")
        return
    bot = FaceitBot()
    bot.add_cog(StatsCommand(bot))
    logger.info("Starting Faceit Discord Bot...")
    bot.run(token)


if __name__ == "__main__":
    main()
