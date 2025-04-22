"""
Type-safe, high-level Python SDK for the official [FACEIT REST API](https://docs.faceit.com/docs/).

See usage examples and documentation: https://github.com/zombyacoff/faceit-python
"""

from ._faceit import AsyncFaceit as AsyncFaceit
from ._faceit import Faceit as Faceit
from ._resources import AsyncPageIterator as AsyncPageIterator
from ._resources import CollectReturnFormat as CollectReturnFormat
from ._resources import MaxItems as MaxItems
from ._resources import MaxPages as MaxPages
from ._resources import SyncPageIterator as SyncPageIterator
from ._resources import check_pagination_support as check_pagination_support
from ._version import __version__ as __version__
from .constants import EventCategory as EventCategory
from .constants import ExpandedField as ExpandedField
from .constants import GameID as GameID
from .constants import Region as Region
from .constants import SkillLevel as SkillLevel
from .http import MaxConcurrentRequests as MaxConcurrentRequests
