from __future__ import annotations

import typing as t
from abc import ABC
from warnings import warn

from ._resources import AsyncDataResource, SyncDataResource
from ._typing import ClientT, DataT, ValidUUID
from .http import AsyncClient, SyncClient


class BaseFaceit(t.Generic[ClientT, DataT], ABC):
    __slots__ = ()

    _client_cls: t.Type[ClientT]
    _data_cls: t.Type[DataT]

    def __new__(cls) -> t.NoReturn:
        """Prevent direct instantiation."""
        raise TypeError(
            f"Direct instantiation of {cls.__name__} is not allowed. "
            f"Use classmethods or factory methods instead."
        )

    @t.overload
    @classmethod
    def data(cls, api_key: ValidUUID, **client_options: t.Any) -> DataT: ...

    @t.overload
    @classmethod
    def data(cls, *, client: ClientT) -> DataT: ...

    @classmethod
    def data(
        cls,
        api_key: t.Optional[ValidUUID] = None,
        *,
        client: t.Optional[ClientT] = None,
        **client_options: t.Any,
    ) -> DataT:
        """
        Create and return a Faceit API data resource.

        You must provide either an `api_key` or a pre-configured HTTP client instance—never both.

        If `api_key` is supplied, a new HTTP client will be initialized with the given options.
        If `client` is supplied, any `client_options` are ignored.

        Refer to the [Faceit API documentation](https://docs.faceit.com) and
        [API key instructions](https://docs.faceit.com/getting-started/authentication/api-keys)
        for details.

        Args:
            api_key: FACEIT API key (str, UUID, or bytes). Used to create a new HTTP client.
            client: Pre-configured HTTP client instance. Cannot be combined with `api_key`.
            **client_options: Additional keyword arguments for HTTP client initialization
                (e.g., timeouts, proxies). Ignored if `client` is provided.

        Returns:
            A ready-to-use Faceit API data resource instance.

        Examples:
            >>> # Synchronous usage with an API key
            >>> data = Faceit.data("YOUR_API_KEY")
            >>> player = data.players.get("s1mple")

            >>> # Synchronous usage with a pre-configured client
            >>> sync_client = SyncClient("YOUR_API_KEY", timeout=10)
            >>> data = Faceit.data(client=sync_client)

            >>> # Asynchronous usage with an API key
            >>> data = AsyncFaceit.data("YOUR_API_KEY")
            >>> player = await data.players.get("s1mple")
        """
        return cls._data_cls(
            cls._initialize_client(
                "api_key", client, auth=api_key, **client_options
            )
        )

    # TODO: The client initialization logic should be revisited when support
    # for API resources beyond Data is introduced.
    @classmethod
    def _initialize_client(
        cls,
        auth_name: str,
        client: t.Optional[ClientT] = None,
        /,
        *,
        auth: t.Optional[ValidUUID] = None,
        **client_options: t.Any,
    ) -> ClientT:
        if auth is None and client is None:
            raise ValueError(
                f"Either '{auth_name}' or 'client' must be provided"
            )

        if auth is not None and client is not None:
            raise ValueError(
                f"Provide either '{auth_name}' or 'client', not both"
            )

        if client is None:
            return cls._client_cls(auth, **client_options)

        if client_options:
            warn(
                "'client_options' are ignored when an existing client "
                "instance is provided. Configure your client before "
                "passing it to this constructor.",
                UserWarning,
                stacklevel=3,
            )

        return client


@t.final
class Faceit(BaseFaceit[SyncClient, SyncDataResource]):
    """
    Synchronous Faceit API interface.

    Example::

        from faceit import Faceit

        with Faceit.data("YOUR_API_KEY") as f:
            player = f.players.get("s1mple")
            assert player.nickname == "s1mple"
    """

    __slots__ = ()
    _client_cls = SyncClient
    _data_cls = SyncDataResource


@t.final
class AsyncFaceit(BaseFaceit[AsyncClient, AsyncDataResource]):
    """
    Asynchronous Faceit API interface.

    Example::

        from faceit import AsyncFaceit

        async with AsyncFaceit.data("YOUR_API_KEY") as f:
            player = await f.players.get("s1mple")
            assert player.nickname == "s1mple"
    """

    __slots__ = ()
    _client_cls = AsyncClient
    _data_cls = AsyncDataResource
