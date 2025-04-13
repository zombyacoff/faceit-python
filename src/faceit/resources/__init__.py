import typing as t
from abc import ABC
from functools import cached_property

from faceit import _repr
from faceit._types import ClientT, Model, Raw
from faceit.http import AsyncClient, SyncClient

from .players import AsyncPlayers, SyncPlayers

__all__ = "AsyncResources", "BaseResources", "SyncResources"


@_repr.representation()
class BaseResources(t.Generic[ClientT], ABC):
    def __init__(self, client: ClientT) -> None:
        self._client = client

    def __str__(self) -> str:
        return f"{self.__class__.__name__} with {self._client}"


@t.final
class SyncResources(BaseResources[SyncClient]):
    @cached_property
    def raw_players(self) -> SyncPlayers[Raw]:
        return SyncPlayers(self._client, raw=True)

    @cached_property
    def players(self) -> SyncPlayers[Model]:
        return SyncPlayers(self._client, raw=False)


@t.final
class AsyncResources(BaseResources[AsyncClient]):
    @cached_property
    def raw_players(self) -> AsyncPlayers[Raw]:
        return AsyncPlayers(self._client, raw=True)

    @cached_property
    def players(self) -> AsyncPlayers[Model]:
        return AsyncPlayers(self._client, raw=False)
