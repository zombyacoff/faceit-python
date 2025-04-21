import typing as t

from faceit._typing import ClientT as ClientT
from faceit._typing import Model as Model
from faceit._typing import Raw as Raw
from faceit.http import AsyncClient as AsyncClient
from faceit.http import SyncClient as SyncClient

from ._aggregator_factory import BaseResources as BaseResources
from ._aggregator_factory import resource_aggregator as _resource_aggregator
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
from ._pagination import MaxItems as MaxItems
from ._pagination import MaxPages as MaxPages
from ._pagination import SyncPageIterator as SyncPageIterator
from ._pagination import TimestampPaginationConfig as TimestampPaginationConfig
from ._pagination import check_pagination_support as check_pagination_support
from ._players import AsyncPlayers as AsyncPlayers
from ._players import BasePlayers as BasePlayers
from ._players import SyncPlayers as SyncPlayers
from ._rankings import AsyncRankings as AsyncRankings
from ._rankings import BaseRankings as BaseRankings
from ._rankings import SyncRankings as SyncRankings
from ._teams import AsyncTeams as AsyncTeams
from ._teams import BaseTeams as BaseTeams
from ._teams import SyncTeams as SyncTeams


@t.final
@_resource_aggregator
class SyncResources(BaseResources[SyncClient]):
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
class AsyncResources(BaseResources[AsyncClient]):
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
