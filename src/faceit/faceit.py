import typing

from typing_extensions import deprecated

from .http import AsyncClient, SyncClient
from .resources import AsyncDataResource, SyncDataResource
from .types import ClientT, DataResourceT


class BaseFaceit(typing.Generic[ClientT, DataResourceT]):
    __slots__ = ()

    if typing.TYPE_CHECKING:
        data: typing.Type[DataResourceT]


@deprecated(
    "`Faceit` is deprecated and will be removed in a future release. "
    "Use `SyncDataResource` instead."
)
@typing.final
class Faceit(BaseFaceit[SyncClient, SyncDataResource]):
    __slots__ = ()

    data = SyncDataResource


@deprecated(
    "`AsyncFaceit` is deprecated and will be removed in a future release. "
    "Use `AsyncDataResource` instead."
)
@typing.final
class AsyncFaceit(BaseFaceit[AsyncClient, AsyncDataResource]):
    __slots__ = ()

    data = AsyncDataResource
