"""
FACEIT API Wrapper
~~~~~~~~~~~~~~~~~~

The easiest and most type-safe way to interact with the FACEIT API.
"""

from importlib.metadata import PackageNotFoundError, version

from .api import (
    AsyncDataResource,
    AsyncPageIterator,
    CollectReturnFormat,
    MaxItems,
    SyncDataResource,
    SyncPageIterator,
    TimestampPaginationConfig,
    pages,
)
from .constants import EventCategory, ExpandedField, GameID, Region, SkillLevel
from .http import FromEnv, MaxConcurrentRequests

__all__ = [
    "AsyncDataResource",
    "AsyncPageIterator",
    "CollectReturnFormat",
    "EventCategory",
    "ExpandedField",
    "FromEnv",
    "GameID",
    "MaxConcurrentRequests",
    "MaxItems",
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
