from __future__ import annotations

from typing import Any

from disnake.ext import commands

import faceit


class FaceitBot(commands.InteractionBot):
    def __init__(self, **kwargs: Any) -> None:
        self.data: faceit.AsyncDataResource | None = None
        super().__init__(**kwargs)

    async def start(self, token: str, *, reconnect: bool = True) -> None:  # type: ignore[override]
        async with faceit.AsyncDataResource() as data:
            self.data = data
            await super().start(token, reconnect=reconnect)
