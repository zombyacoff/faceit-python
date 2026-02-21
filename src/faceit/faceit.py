import typing

from typing_extensions import Self, deprecated

from .http.client import AsyncClient, SyncClient
from .resources import AsyncDataResource, SyncDataResource
from .types import ClientT, DataResourceT


@deprecated("`BaseFaceit` is deprecated and will be removed in a future release.")
class BaseFaceit(typing.Generic[ClientT, DataResourceT]):
    __slots__ = ()

    if typing.TYPE_CHECKING:
        data: typing.Type[DataResourceT]

    def __new__(cls) -> Self:
        raise TypeError(f"Cannot instantiate {cls.__name__} directly.")


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
