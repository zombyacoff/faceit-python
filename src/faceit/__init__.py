# NOTE: This module docstring is provisional and may be revised.
# Suggestions and improvements to the header are welcome.

"""`faceit`: Type-safe, high-level Python SDK for the FACEIT REST API.

Provides a seamless, pythonic interface to FACEIT data with:
- Full static typing and mypy compatibility
- Both synchronous and asynchronous clients
- Pydantic models and advanced pagination utilities
- Idiomatic, reliable abstractions for rapid development

See documentation and usage examples: https://github.com/zombyacoff/faceit
"""

from .__version__ import __version__ as __version__
from ._faceit import AsyncFaceit as AsyncFaceit
from ._faceit import Faceit as Faceit
from ._resources import AsyncPageIterator as AsyncPageIterator
from ._resources import CollectReturnFormat as CollectReturnFormat
from ._resources import SyncPageIterator as SyncPageIterator
from ._resources import check_pagination_support as check_pagination_support
from .constants import EventCategory as EventCategory
from .constants import ExpandOption as ExpandOption
from .constants import GameID as GameID
from .constants import Region as Region
from .constants import SkillLevel as SkillLevel
from .http import AsyncClient as AsyncClient
from .http import SyncClient as SyncClient
