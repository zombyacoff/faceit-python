from typing import final  # noqa: ICN003

from faceit.resources.resource_aggregator import (
    AsyncResources,
    SyncResources,
    resource_aggregator,
)
from faceit.types import Model, Raw

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


@final
@resource_aggregator
class SyncDataResource(SyncResources):
    """Aggregates all synchronous FACEIT Data API resources.

    Each attribute provides access to a resource corresponding to a specific API endpoint.
    Both parsed (``Model``) and raw (``Raw``) data variants are available.

    .. seealso::
        FACEIT Data API documentation: https://docs.faceit.com/docs/data-api/data/
    """

    championships: SyncChampionships[Model]
    """Synchronous resource for the ``/championships`` endpoint.

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Championships
    """

    raw_championships: SyncChampionships[Raw]
    """Synchronous resource for the ``/championships`` endpoint (raw data).

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Championships
    """

    leagues: SyncLeagues[Model]
    """Synchronous resource for the ``/leagues`` endpoint.

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Leagues
    """

    raw_leagues: SyncLeagues[Raw]
    """Synchronous resource for the ``/leagues`` endpoint (raw data).

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Leagues
    """

    matches: SyncMatches[Model]
    """Synchronous resource for the ``/matches`` endpoint.

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Matches
    """

    raw_matches: SyncMatches[Raw]
    """Synchronous resource for the ``/matches`` endpoint (raw data).

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Matches
    """

    matchmakings: SyncMatchmakings[Model]
    """Synchronous resource for the ``/matchmakings`` endpoint.

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Matchmakings
    """

    raw_matchmakings: SyncMatchmakings[Raw]
    """Synchronous resource for the ``/matchmakings`` endpoint (raw data).

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Matchmakings
    """

    players: SyncPlayers[Model]
    """Synchronous resource for the ``/players`` endpoint.

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Players
    """

    raw_players: SyncPlayers[Raw]
    """Synchronous resource for the ``/players`` endpoint (raw data).

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Players
    """

    rankings: SyncRankings[Model]
    """Synchronous resource for the ``/rankings`` endpoint.

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Rankings
    """

    raw_rankings: SyncRankings[Raw]
    """Synchronous resource for the ``/rankings`` endpoint (raw data).

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Rankings
    """

    teams: SyncTeams[Model]
    """Synchronous resource for the ``/teams`` endpoint.

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Teams
    """

    raw_teams: SyncTeams[Raw]
    """Synchronous resource for the ``/teams`` endpoint (raw data).

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Teams
    """


@final
@resource_aggregator
class AsyncDataResource(AsyncResources):
    """Aggregates all asynchronous FACEIT Data API resources.

    Each attribute provides access to a resource corresponding to a specific API endpoint.
    Both parsed (``Model``) and raw (``Raw``) data variants are available.

    .. seealso::
        FACEIT Data API documentation: https://docs.faceit.com/docs/data-api/data/
    """

    championships: AsyncChampionships[Model]
    """Asynchronous resource for the ``/championships`` endpoint.

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Championships
    """

    raw_championships: AsyncChampionships[Raw]
    """Asynchronous resource for the ``/championships`` endpoint (raw data).

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Championships
    """

    matches: AsyncMatches[Model]
    """Asynchronous resource for the ``/matches`` endpoint.

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Matches
    """

    raw_matches: AsyncMatches[Raw]
    """Asynchronous resource for the ``/matches`` endpoint (raw data).

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Matches
    """

    players: AsyncPlayers[Model]
    """Asynchronous resource for the ``/players`` endpoint.

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Players
    """

    raw_players: AsyncPlayers[Raw]
    """Asynchronous resource for the ``/players`` endpoint (raw data).

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Players
    """

    teams: AsyncTeams[Model]
    """Asynchronous resource for the ``/teams`` endpoint.

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Teams
    """

    raw_teams: AsyncTeams[Raw]
    """Asynchronous resource for the ``/teams`` endpoint (raw data).

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Teams
    """

    rankings: AsyncRankings[Model]
    """Asynchronous resource for the ``/rankings`` endpoint.

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Rankings
    """

    raw_rankings: AsyncRankings[Raw]
    """Asynchronous resource for the ``/rankings`` endpoint (raw data).

    For details, see:
    https://docs.faceit.com/docs/data-api/data/#tag/Rankings
    """
