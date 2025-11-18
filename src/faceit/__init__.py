from importlib.metadata import PackageNotFoundError, version

from .constants import EventCategory, ExpandedField, GameID, Region, SkillLevel
from .exceptions import (
    APIError,
    DecoupleMissingError,
    FaceitError,
    MissingAuthTokenError,
)
from .http import EnvKey, MaxConcurrentRequests
from .resources import (
    AsyncDataResource,
    AsyncPageIterator,
    CollectReturnFormat,
    MaxItems,
    MaxPages,
    SyncDataResource,
    SyncPageIterator,
    TimestampPaginationConfig,
    pages,
)

__all__ = [
    "APIError",
    "AsyncDataResource",
    "AsyncPageIterator",
    "CollectReturnFormat",
    "DecoupleMissingError",
    "EnvKey",
    "EventCategory",
    "ExpandedField",
    "FaceitError",
    "GameID",
    "MaxConcurrentRequests",
    "MaxItems",
    "MaxPages",
    "MissingAuthTokenError",
    "Region",
    "SkillLevel",
    "SyncDataResource",
    "SyncPageIterator",
    "TimestampPaginationConfig",
    "__version__",
    "pages",
]

try:
    __version__ = version(__package__ or __name__)
except PackageNotFoundError:
    __version__ = "0.0.0"

del PackageNotFoundError, version
