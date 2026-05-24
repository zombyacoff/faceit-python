"""
FACEIT API Wrapper
~~~~~~~~~~~~~~~~~~

The easiest and most type-safe way to interact with the FACEIT API.
"""

from importlib.metadata import PackageNotFoundError, version

from .api import (
    AsyncDataResource as AsyncDataResource,
    AsyncPageIterator as AsyncPageIterator,
    SyncDataResource as SyncDataResource,
    SyncPageIterator as SyncPageIterator,
    TimestampPaginationConfig as TimestampPaginationConfig,
    pages as pages,
)
from .constants import (
    EventCategory as EventCategory,
    ExpandedField as ExpandedField,
    GameID as GameID,
    Region as Region,
    SkillLevel as SkillLevel,
)
from .exceptions import (
    APIError as APIError,
    BadRequestError as BadRequestError,
    DecoupleNotFoundError as DecoupleNotFoundError,
    FaceitError as FaceitError,
    ForbiddenError as ForbiddenError,
    InternalServerError as InternalServerError,
    MissingAuthTokenError as MissingAuthTokenError,
    NotFoundError as NotFoundError,
    ServiceUnavailableError as ServiceUnavailableError,
    TooManyRequestsError as TooManyRequestsError,
    UnauthorizedError as UnauthorizedError,
)
from .http import FromEnv as FromEnv

try:
    __version__ = version(__package__ or __name__)
except PackageNotFoundError:
    __version__ = "0.0.0"

del PackageNotFoundError, version
