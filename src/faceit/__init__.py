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
from .exceptions import APIError, FaceitError  # deprecated import
from .faceit import AsyncFaceit, Faceit
from .http import EnvKey, FromEnv, MaxConcurrentRequests

__all__ = [
    "APIError",
    "AsyncDataResource",
    "AsyncFaceit",  # deprecated (remove in v0.3.0 ?)
    "AsyncPageIterator",
    "CollectReturnFormat",
    "EnvKey",  # deprecated (remove in v0.2.2 ?)
    "EventCategory",
    "ExpandedField",
    "Faceit",  # deprecated (remove in v0.3.0 ?)
    "FaceitError",
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
