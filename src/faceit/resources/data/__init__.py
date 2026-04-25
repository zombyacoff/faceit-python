import typing

from faceit.http.client import BaseAPIClient
from faceit.resources.aggregator import (
    AsyncResources,
    BaseResources,
    SyncResources,
    resource_aggregator,
)
from faceit.types import ClientT, Model, Raw, ValidUUID

from .championships import AsyncChampionships, BaseChampionships, SyncChampionships
from .games import AsyncGames, BaseGames, SyncGames
from .leagues import AsyncLeagues, BaseLeagues, SyncLeagues
from .matches import AsyncMatches, BaseMatches, SyncMatches
from .matchmakings import AsyncMatchmakings, BaseMatchmakings, SyncMatchmakings
from .players import AsyncPlayers, BasePlayers, SyncPlayers
from .rankings import AsyncRankings, BaseRankings, SyncRankings
from .teams import AsyncTeams, BaseTeams, SyncTeams

__all__ = [
    "AsyncChampionships",
    "AsyncDataResource",
    "AsyncGames",
    "AsyncLeagues",
    "AsyncMatches",
    "AsyncMatchmakings",
    "AsyncPlayers",
    "AsyncRankings",
    "AsyncTeams",
    "BaseChampionships",
    "BaseGames",
    "BaseLeagues",
    "BaseMatches",
    "BaseMatchmakings",
    "BasePlayers",
    "BaseRankings",
    "BaseTeams",
    "SyncChampionships",
    "SyncDataResource",
    "SyncGames",
    "SyncLeagues",
    "SyncMatches",
    "SyncMatchmakings",
    "SyncPlayers",
    "SyncRankings",
    "SyncTeams",
]


class _DataResourceMixin:
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

    def __init__(  # type: ignore[misc]
        self: BaseResources[ClientT],
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


@typing.final
@resource_aggregator
class SyncDataResource(SyncResources, _DataResourceMixin):
    championships: SyncChampionships[Model]
    raw_championships: SyncChampionships[Raw]

    games: SyncGames[Model]
    raw_games: SyncGames[Raw]

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

    games: AsyncGames[Model]
    raw_games: AsyncGames[Raw]

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
