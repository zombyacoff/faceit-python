import typing
import warnings

from typing_extensions import deprecated

from .http import AsyncClient, SyncClient
from .resources import AsyncDataResource, SyncDataResource
from .types import ClientT, DataResourceT


class BaseFaceit(typing.Generic[ClientT, DataResourceT]):
    __slots__ = ()

    if typing.TYPE_CHECKING:
        _data_cls: typing.Type[DataResourceT]

    @classmethod
    def data(cls, *args: typing.Any, **kwargs: typing.Any) -> DataResourceT:
        warnings.warn(
            f"`{cls.__name__}.data()` is deprecated and will be removed in a future release. "
            f"Please instantiate `{cls._data_cls.__name__}` directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        return typing.cast("DataResourceT", cls._data_cls(*args, **kwargs))


@typing.final
@deprecated(
    "`Faceit` is deprecated and will be removed in a future release. "
    "Use `SyncDataResource` instead."
)
class Faceit(BaseFaceit[SyncClient, SyncDataResource]):
    __slots__ = ()

    _data_cls = SyncDataResource


@typing.final
@deprecated(
    "`AsyncFaceit` is deprecated and will be removed in a future release. "
    "Use `AsyncDataResource` instead."
)
class AsyncFaceit(BaseFaceit[AsyncClient, AsyncDataResource]):
    __slots__ = ()

    _data_cls = AsyncDataResource
