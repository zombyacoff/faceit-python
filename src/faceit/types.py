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

from ._faceit import BaseFaceit
from ._resources import (
    AsyncChampionships,
    AsyncMatches,
    AsyncPlayers,
    BaseChampionships,
    BaseMatches,
    BasePageIterator,
    BasePlayers,
    BaseResource,
    BaseResources,
    SyncChampionships,
    SyncMatches,
    SyncPlayers,
    TimestampPaginationConfig,
)
from ._typing import (
    AsyncPaginationMethod,
    AsyncUnixPaginationMethod,
    BasePaginationMethod,
    BaseUnixPaginationMethod,
    EndpointParam,
    Model,
    Raw,
    RawAPIItem,
    RawAPIPageResponse,
    RawAPIResponse,
    SyncPaginationMethod,
    SyncUnixPaginationMethod,
)
from .constants import EloRange
from .http._client import BaseAPIClient
from .models._custom_types import (
    FaceitID,
    FaceitMatchID,
    FaceitTeamID,
    NullableList,
    ResponseContainer,
)
from .models._custom_types._faceit_uuid import BaseFaceitID
from .models._page import PaginationMetadata, PaginationTimeRange

__all__ = (
    "AsyncChampionships",
    "AsyncMatches",
    "AsyncPaginationMethod",
    "AsyncPlayers",
    "AsyncUnixPaginationMethod",
    "BaseAPIClient",
    "BaseChampionships",
    "BaseFaceit",
    "BaseFaceitID",
    "BaseMatches",
    "BasePageIterator",
    "BasePaginationMethod",
    "BasePlayers",
    "BaseResource",
    "BaseResources",
    "BaseUnixPaginationMethod",
    "EloRange",
    "EndpointParam",
    "FaceitID",
    "FaceitMatchID",
    "FaceitTeamID",
    "Model",
    "NullableList",
    "PaginationMetadata",
    "PaginationTimeRange",
    "Raw",
    "RawAPIItem",
    "RawAPIPageResponse",
    "RawAPIResponse",
    "ResponseContainer",
    "SyncChampionships",
    "SyncMatches",
    "SyncPaginationMethod",
    "SyncPlayers",
    "SyncUnixPaginationMethod",
    "TimestampPaginationConfig",
)
