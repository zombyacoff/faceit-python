from typing import final, overload

from faceit.api.aggregator import (
    AsyncResources,
    BaseResources,
    SyncResources,
    resource_aggregator,
)
from faceit.http.client import BaseAPIClient
from faceit.types import ClientT, Model, Raw, ValidUUID

from .championships import (
    AsyncChampionships as AsyncChampionships,
    BaseChampionships as BaseChampionships,
    SyncChampionships as SyncChampionships,
)
from .games import (
    AsyncGames as AsyncGames,
    BaseGames as BaseGames,
    SyncGames as SyncGames,
)
from .leagues import (
    AsyncLeagues as AsyncLeagues,
    BaseLeagues as BaseLeagues,
    SyncLeagues as SyncLeagues,
)
from .matches import (
    AsyncMatches as AsyncMatches,
    BaseMatches as BaseMatches,
    SyncMatches as SyncMatches,
)
from .matchmakings import (
    AsyncMatchmakings as AsyncMatchmakings,
    BaseMatchmakings as BaseMatchmakings,
    SyncMatchmakings as SyncMatchmakings,
)
from .players import (
    AsyncPlayers as AsyncPlayers,
    BasePlayers as BasePlayers,
    SyncPlayers as SyncPlayers,
)
from .rankings import (
    AsyncRankings as AsyncRankings,
    BaseRankings as BaseRankings,
    SyncRankings as SyncRankings,
)
from .teams import (
    AsyncTeams as AsyncTeams,
    BaseTeams as BaseTeams,
    SyncTeams as SyncTeams,
)


class _DataResourceMixin:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self: BaseResources[ClientT], *, client: ClientT) -> None: ...  # type: ignore[misc]

    @overload
    def __init__(self, api_key: ValidUUID | BaseAPIClient.env) -> None: ...

    def __init__(  # type: ignore[misc]
        self: BaseResources[ClientT],  # pyright: ignore[reportGeneralTypeIssues]
        api_key: ValidUUID | BaseAPIClient.env | None = None,
        *,
        client: ClientT | None = None,
    ) -> None:
        self._initialize_client(api_key, client, secret_type="api_key")  # noqa: S106


@final
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


@final
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
