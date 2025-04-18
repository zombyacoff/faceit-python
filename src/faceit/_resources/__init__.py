import typing as t
from abc import ABC
from dataclasses import dataclass
from functools import cached_property

from faceit._typing import ClientT, Model, Raw
from faceit.http import AsyncClient, SyncClient

from ._base import BaseResource
from ._championships import (
    AsyncChampionships,
    BaseChampionships,
    SyncChampionships,
)
from ._matches import AsyncMatches, BaseMatches, SyncMatches
from ._pagination import (
    AsyncPageIterator,
    BasePageIterator,
    CollectReturnFormat,
    SyncPageIterator,
    TimestampPaginationConfig,
    check_pagination_support,
)
from ._players import AsyncPlayers, BasePlayers, SyncPlayers

__all__ = (
    "AsyncChampionships",
    "AsyncMatches",
    "AsyncPageIterator",
    "AsyncPlayers",
    "AsyncResources",
    "BaseChampionships",
    "BaseMatches",
    "BasePageIterator",
    "BasePlayers",
    "BaseResource",
    "BaseResources",
    "CollectReturnFormat",
    "SyncChampionships",
    "SyncMatches",
    "SyncPageIterator",
    "SyncPlayers",
    "SyncResources",
    "TimestampPaginationConfig",
    "check_pagination_support",
)


@dataclass(eq=False, frozen=True)
class BaseResources(t.Generic[ClientT], ABC):
    _client: ClientT


@t.final
class SyncResources(BaseResources[SyncClient]):
    @cached_property
    def raw_championships(self) -> SyncChampionships[Raw]:
        return SyncChampionships(self._client, raw=True)

    @cached_property
    def championships(self) -> SyncChampionships[Model]:
        return SyncChampionships(self._client, raw=False)

    @cached_property
    def raw_matches(self) -> SyncMatches[Raw]:
        return SyncMatches(self._client, raw=True)

    @cached_property
    def matches(self) -> SyncMatches[Model]:
        return SyncMatches(self._client, raw=False)

    @cached_property
    def raw_players(self) -> SyncPlayers[Raw]:
        return SyncPlayers(self._client, raw=True)

    @cached_property
    def players(self) -> SyncPlayers[Model]:
        return SyncPlayers(self._client, raw=False)


@t.final
class AsyncResources(BaseResources[AsyncClient]):
    @cached_property
    def raw_championships(self) -> AsyncChampionships[Raw]:
        return AsyncChampionships(self._client, raw=True)

    @cached_property
    def championships(self) -> AsyncChampionships[Model]:
        return AsyncChampionships(self._client, raw=False)

    @cached_property
    def raw_matches(self) -> AsyncMatches[Raw]:
        return AsyncMatches(self._client, raw=True)

    @cached_property
    def matches(self) -> AsyncMatches[Model]:
        return AsyncMatches(self._client, raw=False)

    @cached_property
    def raw_players(self) -> AsyncPlayers[Raw]:
        return AsyncPlayers(self._client, raw=True)

    @cached_property
    def players(self) -> AsyncPlayers[Model]:
        return AsyncPlayers(self._client, raw=False)
