import typing
from abc import ABC, abstractmethod

from faceit.http.client import BaseAPIClient
from faceit.resources.aggregator import (
    AsyncResources,
    SyncResources,
    resource_aggregator,
)
from faceit.types import ClientT, Model, Raw, ValidUUID

from .championships import AsyncChampionships as AsyncChampionships
from .championships import BaseChampionships as BaseChampionships
from .championships import SyncChampionships as SyncChampionships
from .leagues import AsyncLeagues as AsyncLeagues
from .leagues import BaseLeagues as BaseLeagues
from .leagues import SyncLeagues as SyncLeagues
from .matches import AsyncMatches as AsyncMatches
from .matches import BaseMatches as BaseMatches
from .matches import SyncMatches as SyncMatches
from .matchmakings import AsyncMatchmakings as AsyncMatchmakings
from .matchmakings import BaseMatchmakings as BaseMatchmakings
from .matchmakings import SyncMatchmakings as SyncMatchmakings
from .players import AsyncPlayers as AsyncPlayers
from .players import BasePlayers as BasePlayers
from .players import SyncPlayers as SyncPlayers
from .rankings import AsyncRankings as AsyncRankings
from .rankings import BaseRankings as BaseRankings
from .rankings import SyncRankings as SyncRankings
from .teams import AsyncTeams as AsyncTeams
from .teams import BaseTeams as BaseTeams
from .teams import SyncTeams as SyncTeams


class _DataResourceMixin(ABC):
    @typing.overload
    def __init__(self) -> None: ...

    @typing.overload
    def __init__(self, *, client: ClientT) -> None: ...

    @typing.overload
    def __init__(
        self,
        api_key: typing.Union[ValidUUID, BaseAPIClient.env],
        **client_options: typing.Any,
    ) -> None: ...

    def __init__(
        self,
        api_key: typing.Union[ValidUUID, BaseAPIClient.env, None] = None,
        *,
        client: typing.Optional[ClientT] = None,
        **client_options: typing.Any,
    ) -> None:
        self._initialize_client(
            api_key,
            client,
            secret_type="api_key",  # noqa: S106
            **client_options,
        )

    @abstractmethod
    def _initialize_client(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        pass


@typing.final
@resource_aggregator
class SyncDataResource(SyncResources, _DataResourceMixin):
    championships: SyncChampionships[Model]
    raw_championships: SyncChampionships[Raw]

    leagues: SyncLeagues[Model]
    raw_leagues: SyncLeagues[Raw]

    matches: SyncMatches[Model]
    raw_matches: SyncMatches[Raw]

    matchmakings: SyncMatchmakings[Model]
    raw_matchmakings: SyncMatchmakings[Raw]

    players: SyncPlayers[Model]
    raw_players: SyncPlayers[Raw]

    rankings: SyncRankings[Model]
    raw_rankings: SyncRankings[Raw]

    teams: SyncTeams[Model]
    raw_teams: SyncTeams[Raw]


@typing.final
@resource_aggregator
class AsyncDataResource(AsyncResources, _DataResourceMixin):
    championships: AsyncChampionships[Model]
    raw_championships: AsyncChampionships[Raw]

    leagues: AsyncLeagues[Model]
    raw_leagues: AsyncLeagues[Raw]

    matches: AsyncMatches[Model]
    raw_matches: AsyncMatches[Raw]

    matchmakings: AsyncMatchmakings[Model]
    raw_matchmakings: AsyncMatchmakings[Raw]

    players: AsyncPlayers[Model]
    raw_players: AsyncPlayers[Raw]

    teams: AsyncTeams[Model]
    raw_teams: AsyncTeams[Raw]

    rankings: AsyncRankings[Model]
    raw_rankings: AsyncRankings[Raw]
