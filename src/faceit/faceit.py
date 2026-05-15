from typing import TYPE_CHECKING, Any, Generic, cast, final

from typing_extensions import deprecated

from .api import AsyncDataResource, SyncDataResource
from .http import AsyncClient, SyncClient
from .types import ClientT, DataResourceT


class BaseFaceit(Generic[ClientT, DataResourceT]):
    __slots__ = ()

    if TYPE_CHECKING:
        _data_cls: type[DataResourceT]

    @classmethod
    def data(cls, *args: Any, **kwargs: Any) -> DataResourceT:
        import warnings  # noqa: PLC0415

        warnings.warn(
            f"`{cls.__name__}.data()` is deprecated and will be removed in a future release. "
            f"Please instantiate `{cls._data_cls.__name__}` directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        return cast("DataResourceT", cls._data_cls(*args, **kwargs))


@final
@deprecated(
    "`Faceit` is deprecated and will be removed in a future release. "
    "Use `SyncDataResource` instead."
)
class Faceit(BaseFaceit[SyncClient, SyncDataResource]):
    __slots__ = ()

    _data_cls = SyncDataResource


@final
@deprecated(
    "`AsyncFaceit` is deprecated and will be removed in a future release. "
    "Use `AsyncDataResource` instead."
)
class AsyncFaceit(BaseFaceit[AsyncClient, AsyncDataResource]):
    __slots__ = ()

    _data_cls = AsyncDataResource
