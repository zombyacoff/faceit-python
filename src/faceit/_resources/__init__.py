import typing as t

from faceit._typing import Model, Raw
from faceit.http import AsyncClient, SyncClient

from .aggregator_factory import BaseResources as BaseResources
from .aggregator_factory import resource_aggregator as _resource_aggregator
from .base import BaseResource as BaseResource
from .data import AsyncChampionships as AsyncChampionships
from .data import AsyncMatches as AsyncMatches
from .data import AsyncPlayers as AsyncPlayers
from .data import AsyncRankings as AsyncRankings
from .data import AsyncTeams as AsyncTeams
from .data import BaseChampionships as BaseChampionships
from .data import BaseMatches as BaseMatches
from .data import BasePlayers as BasePlayers
from .data import BaseRankings as BaseRankings
from .data import BaseTeams as BaseTeams
from .data import SyncChampionships as SyncChampionships
from .data import SyncMatches as SyncMatches
from .data import SyncPlayers as SyncPlayers
from .data import SyncRankings as SyncRankings
from .data import SyncTeams as SyncTeams
from .pagination import AsyncPageIterator as AsyncPageIterator
from .pagination import BasePageIterator as BasePageIterator
from .pagination import CollectReturnFormat as CollectReturnFormat
from .pagination import MaxItems as MaxItems
from .pagination import MaxPages as MaxPages
from .pagination import SyncPageIterator as SyncPageIterator
from .pagination import TimestampPaginationConfig as TimestampPaginationConfig
from .pagination import check_pagination_support as check_pagination_support


@t.final
@_resource_aggregator
class SyncData(BaseResources[SyncClient]):
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


@t.final
@_resource_aggregator
class AsyncData(BaseResources[AsyncClient]):
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
