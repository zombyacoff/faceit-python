from __future__ import annotations

import typing
from abc import ABC
from functools import lru_cache
from warnings import warn

from typing_extensions import Self

from .http import AsyncClient, EnvKey, SyncClient
from .resources import AsyncDataResource, SyncDataResource
from .types import ClientT, DataResourceT, ValidUUID

if typing.TYPE_CHECKING:
    from .http.client import BaseAPIClient


@lru_cache(maxsize=None)
def _get_env_key(key: str, /) -> BaseAPIClient.env:
    return EnvKey(f"FACEIT_{key.upper()}")


class BaseFaceit(ABC, typing.Generic[ClientT, DataResourceT]):
    __slots__ = ()

    if typing.TYPE_CHECKING:
        _client_cls: typing.Type[ClientT]
        _data_cls: typing.Type[DataResourceT]

    def __new__(cls) -> Self:
        raise TypeError(
            f"Cannot instantiate {cls.__name__} directly. "
            "Please use the provided classmethods or factory methods (e.g., `data()`) "
            "to obtain an instance. Direct instantiation is intentionally disabled "
            "to enforce correct usage patterns."
        )

    @typing.overload
    @classmethod
    def data(cls) -> DataResourceT: ...

    @typing.overload
    @classmethod
    def data(cls, *, client: ClientT) -> DataResourceT: ...

    @typing.overload
    @classmethod
    def data(
        cls,
        api_key: typing.Union[ValidUUID, BaseAPIClient.env],
        **client_options: typing.Any,
    ) -> DataResourceT: ...

    @classmethod
    def data(
        cls,
        api_key: typing.Union[ValidUUID, BaseAPIClient.env, None] = None,
        *,
        client: typing.Optional[ClientT] = None,
        **client_options: typing.Any,
    ) -> DataResourceT:
        return typing.cast(
            "DataResourceT",
            cls._data_cls(
                cls._initialize_client(
                    api_key, client, secret_type="api_key", **client_options
                )
            ),
        )

    # TODO: The client initialization logic should be revisited when support
    # for API resources beyond Data is introduced.
    @classmethod
    def _initialize_client(
        cls,
        auth: typing.Union[ValidUUID, BaseAPIClient.env, None] = None,
        client: typing.Optional[ClientT] = None,
        /,
        *,
        secret_type: str,
        **client_options: typing.Any,
    ) -> ClientT:
        if auth is not None and client is not None:
            raise ValueError(f"Provide either {secret_type!r} or 'client', not both")

        if client is None:
            return typing.cast(
                "ClientT",
                cls._client_cls(
                    _get_env_key(secret_type) if auth is None else auth,
                    **client_options,
                ),
            )

        if client_options:
            warn(
                "'client_options' are ignored when an existing client "
                "instance is provided. Configure your client before "
                "passing it to this constructor.",
                UserWarning,
                stacklevel=3,
            )

        return client


@typing.final
class Faceit(BaseFaceit[SyncClient, SyncDataResource]):
    """
    Synchronous Faceit API interface.

    Example (Data API)::

        with Faceit.data("YOUR_API_KEY") as data:
            player = data.players.get("s1mple")
            assert player.nickname == "s1mple"

    This class uses a synchronous HTTP client under the hood.
    """

    __slots__ = ()
    _client_cls = SyncClient
    _data_cls = SyncDataResource


@typing.final
class AsyncFaceit(BaseFaceit[AsyncClient, AsyncDataResource]):
    """
    Asynchronous Faceit API interface.

    Example (Data API)::

        async with AsyncFaceit.data("YOUR_API_KEY") as data:
            player = await data.players.get("s1mple")
            assert player.nickname == "s1mple"

    This class uses an asynchronous HTTP client under the hood.
    """

    __slots__ = ()
    _client_cls = AsyncClient
    _data_cls = AsyncDataResource
