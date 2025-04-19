import typing as t
from abc import ABC
from dataclasses import dataclass
from functools import cached_property

from faceit._typing import ClientT as ClientT
from faceit._typing import Model as Model
from faceit._typing import Raw as Raw
from faceit.http import AsyncClient as AsyncClient
from faceit.http import SyncClient as SyncClient

from ._base import BaseResource as BaseResource
from ._championships import AsyncChampionships as AsyncChampionships
from ._championships import BaseChampionships as BaseChampionships
from ._championships import SyncChampionships as SyncChampionships
from ._matches import AsyncMatches as AsyncMatches
from ._matches import BaseMatches as BaseMatches
from ._matches import SyncMatches as SyncMatches
from ._pagination import AsyncPageIterator as AsyncPageIterator
from ._pagination import BasePageIterator as BasePageIterator
from ._pagination import CollectReturnFormat as CollectReturnFormat
from ._pagination import SyncPageIterator as SyncPageIterator
from ._pagination import TimestampPaginationConfig as TimestampPaginationConfig
from ._pagination import check_pagination_support as check_pagination_support
from ._players import AsyncPlayers as AsyncPlayers
from ._players import BasePlayers as BasePlayers
from ._players import SyncPlayers as SyncPlayers


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
