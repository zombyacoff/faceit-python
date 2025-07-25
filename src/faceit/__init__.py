from importlib.metadata import PackageNotFoundError, version

from .constants import EventCategory as EventCategory
from .constants import ExpandedField as ExpandedField
from .constants import GameID as GameID
from .constants import Region as Region
from .constants import SkillLevel as SkillLevel
from .exceptions import APIError as APIError
from .exceptions import DecoupleMissingError as DecoupleMissingError
from .exceptions import FaceitError as FaceitError
from .exceptions import MissingAuthTokenError as MissingAuthTokenError
from .faceit import AsyncFaceit as AsyncFaceit
from .faceit import Faceit as Faceit
from .http import EnvKey as EnvKey
from .http import MaxConcurrentRequests as MaxConcurrentRequests
from .resources import AsyncPageIterator as AsyncPageIterator
from .resources import CollectReturnFormat as CollectReturnFormat
from .resources import MaxItems as MaxItems
from .resources import MaxPages as MaxPages
from .resources import SyncPageIterator as SyncPageIterator
from .resources import TimestampPaginationConfig as TimestampPaginationConfig
from .resources import pages as pages

try:
    __version__ = version(__package__ or __name__)
except PackageNotFoundError:
    __version__ = "0.0.0"

del PackageNotFoundError, version
