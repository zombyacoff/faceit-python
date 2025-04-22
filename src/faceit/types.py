"""
This module aggregates public types, abstract base classes, and protocols intended
for use by library consumers in type annotations, runtime checks (e.g., isinstance),
and static analysis.

Most types are imported from the internal `_typing.py` module, which handles backports
and compatibility with different Python versions. This separation ensures a clear
distinction between types used for annotations and the core implementation classes
aggregated by the main `__init__.py`.

End users should import types from this module for type hinting and interface checks,
rather than from internal modules or implementation files.
"""

from ._faceit import BaseFaceit as BaseFaceit
from ._resources import AsyncChampionships as AsyncChampionships
from ._resources import AsyncMatches as AsyncMatches
from ._resources import AsyncPlayers as AsyncPlayers
from ._resources import AsyncRankings as AsyncRankings
from ._resources import AsyncTeams as AsyncTeams
from ._resources import BaseChampionships as BaseChampionships
from ._resources import BaseMatches as BaseMatches
from ._resources import BasePageIterator as BasePageIterator
from ._resources import BasePlayers as BasePlayers
from ._resources import BaseRankings as BaseRankings
from ._resources import BaseResource as BaseResource
from ._resources import BaseResources as BaseResources
from ._resources import BaseTeams as BaseTeams
from ._resources import SyncChampionships as SyncChampionships
from ._resources import SyncMatches as SyncMatches
from ._resources import SyncPlayers as SyncPlayers
from ._resources import SyncRankings as SyncRankings
from ._resources import SyncTeams as SyncTeams
from ._resources import TimestampPaginationConfig as TimestampPaginationConfig
from ._typing import AsyncPaginationMethod as AsyncPaginationMethod
from ._typing import AsyncUnixPaginationMethod as AsyncUnixPaginationMethod
from ._typing import BasePaginationMethod as BasePaginationMethod
from ._typing import BaseUnixPaginationMethod as BaseUnixPaginationMethod
from ._typing import EndpointParam as EndpointParam
from ._typing import Model as Model
from ._typing import Raw as Raw
from ._typing import RawAPIItem as RawAPIItem
from ._typing import RawAPIPageResponse as RawAPIPageResponse
from ._typing import RawAPIResponse as RawAPIResponse
from ._typing import SyncPaginationMethod as SyncPaginationMethod
from ._typing import SyncUnixPaginationMethod as SyncUnixPaginationMethod
from .http._client import BaseAPIClient as BaseAPIClient
from .models._custom_types import FaceitID as FaceitID
from .models._custom_types import FaceitMatchID as FaceitMatchID
from .models._custom_types import FaceitTeamID as FaceitTeamID
from .models._custom_types import NullableList as NullableList
from .models._custom_types import ResponseContainer as ResponseContainer
from .models._custom_types.faceit_uuid import BaseFaceitID as BaseFaceitID
from .models._item_page import PaginationMetadata as PaginationMetadata
from .models._item_page import PaginationTimeRange as PaginationTimeRange
from .models.players._match import (
    AbstractMatchPlayerStats as AbstractMatchPlayerStats,
)
