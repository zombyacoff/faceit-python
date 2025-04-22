from typing import final  # noqa: ICN003

from faceit._resources.resource_aggregator import (
    AsyncResources,
    SyncResources,
    resource_aggregator,
)
from faceit._typing import Model, Raw

from .championships import AsyncChampionships as AsyncChampionships
from .championships import BaseChampionships as BaseChampionships
from .championships import SyncChampionships as SyncChampionships
from .matches import AsyncMatches as AsyncMatches
from .matches import BaseMatches as BaseMatches
from .matches import SyncMatches as SyncMatches
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
    championships: SyncChampionships[Model]
    raw_championships: SyncChampionships[Raw]

    matches: SyncMatches[Model]
    raw_matches: SyncMatches[Raw]

    players: SyncPlayers[Model]
    raw_players: SyncPlayers[Raw]

    teams: SyncTeams[Model]
    raw_teams: SyncTeams[Raw]

    rankings: SyncRankings[Model]
    raw_rankings: SyncRankings[Raw]


@final
@resource_aggregator
class AsyncDataResource(AsyncResources):
    championships: AsyncChampionships[Model]
    raw_championships: AsyncChampionships[Raw]

    matches: AsyncMatches[Model]
    raw_matches: AsyncMatches[Raw]

    players: AsyncPlayers[Model]
    raw_players: AsyncPlayers[Raw]

    teams: AsyncTeams[Model]
    raw_teams: AsyncTeams[Raw]

    rankings: AsyncRankings[Model]
    raw_rankings: AsyncRankings[Raw]
