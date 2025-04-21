from __future__ import annotations

import typing as t
from abc import ABC
from warnings import warn

from ._resources import AsyncData, SyncData
from ._typing import ClientT, DataT, Self, ValidUUID, deprecated
from ._utils import representation
from .constants import BASE_WIKI_URL
from .http import AsyncClient, SyncClient

if t.TYPE_CHECKING:
    from types import TracebackType


@representation("client", "data")
class BaseFaceit(t.Generic[ClientT, DataT], ABC):
    __slots__ = ("_client", "_data")

    _client_cls: t.Type[ClientT]

    _chat_cls: None
    _data_cls: t.Type[DataT]
    _webhooks_cls: None

    @t.overload
    def __init__(
        self,
        api_key: ValidUUID,
        **client_options: t.Any,
    ) -> None: ...

    @t.overload
    def __init__(
        self,
        *,
        client: ClientT,
    ) -> None: ...

    def __init__(
        self,
        api_key: t.Optional[ValidUUID] = None,
        *,
        client: t.Optional[ClientT] = None,
        **client_options: t.Any,
    ) -> None:
        """
        Initializes the Faceit API interface.

        You must provide either an `api_key` or a pre-configured HTTP client instance.
        Providing both is not allowed.

        If `api_key` is provided, a new client will be created using the given options.
        If `client` is provided, any additional `client_options` will be ignored.

        See the [Faceit API documentation](https://docs.faceit.com) and
        [how to get an API key](https://docs.faceit.com/getting-started/authentication/api-keys)
        for more information.

        Args:
            api_key: FACEIT API key (Valid UUID: `str`, `UUID`, or `bytes`).
            client: Pre-configured HTTP client instance.
            **client_options: Additional options for client initialization
                (e.g., timeouts, proxies).
        """
        if api_key is None and client is None:
            raise ValueError("Either 'api_key' or 'client' must be provided")
        if api_key is not None and client is not None:
            raise ValueError("Provide either 'api_key' or 'client', not both")

        if client is not None:
            if client_options:
                warn(
                    "'client_options' are ignored when an existing client "
                    "instance is provided. Configure your client before "
                    "passing it to this constructor.",
                    UserWarning,
                    stacklevel=2,
                )
            self._client = client
        else:
            self._client = self.__class__._client_cls(
                api_key, **client_options
            )

        self._data = self.__class__._data_cls(self._client)

    @property
    def client(self) -> ClientT:
        """
        The underlying HTTP client instance for low-level interactions with the
        Faceit API (e.g., unsupported endpoints or advanced use cases).
        """
        return self._client

    @deprecated(
        "For greater clarity and maintainability, we now expose API domains as "
        "explicit properties such as `.data` (and in the future, `.chat`, etc.), "
        "instead of aggregating all resources under a single `.resources` property. "
        "In earlier releases, `.resources` referred only to data-related resources, "
        "but this is now superseded by the `.data` property. Please migrate to using "
        "`.data` for your use case. This alias will be removed at the earliest "
        "opportunity, in an upcoming release."
    )
    @property
    def resources(self) -> DataT:
        """Alias for `.data`. Deprecated."""
        return self._data

    @property
    def chat(self) -> t.NoReturn:
        """
        **Not yet supported.**
        This API resource will be available in a future release.
        """
        raise NotImplementedError

    @property
    def data(self) -> DataT:
        """Provides access to the data API resource (v4)."""
        return self._data

    @property
    def webhooks(self) -> t.NoReturn:
        """
        **Not yet supported.**
        This API resource will be available in a future release.
        """
        raise NotImplementedError

    def __str__(self) -> str:
        return (
            f"FACEIT API interface "
            f"(resources and client, docs: {BASE_WIKI_URL})"
        )


@t.final
class Faceit(BaseFaceit[SyncClient, SyncData]):
    """
    Synchronous Faceit API interface.

    Example::

        from faceit import Faceit

        with Faceit("YOUR_API_KEY") as f:
            player = f.data.players.get("s1mple")
            assert player.nickname == "s1mple"
    """

    __slots__ = ()

    _client_cls = SyncClient

    _chat_cls = None
    _data_cls = SyncData
    _webhooks_cls = None

    def __enter__(self) -> Self:
        self.client.__enter__()
        return self

    def __exit__(
        self,
        typ: t.Optional[t.Type[BaseException]],
        exc: t.Optional[BaseException],
        tb: t.Optional[TracebackType],
    ) -> None:
        self.client.__exit__(typ, exc, tb)


@t.final
class AsyncFaceit(BaseFaceit[AsyncClient, AsyncData]):
    """
    Asynchronous Faceit API interface.

    Example::

        from faceit import AsyncFaceit

        async with AsyncFaceit("YOUR_API_KEY") as f:
            player = await f.data.players.get("s1mple")
            assert player.nickname == "s1mple"
    """

    __slots__ = ()

    _client_cls = AsyncClient

    _chat_cls = None
    _data_cls = AsyncData
    _webhooks_cls = None

    async def __aenter__(self) -> Self:
        await self.client.__aenter__()
        return self

    async def __aexit__(
        self,
        typ: t.Optional[t.Type[BaseException]],
        exc: t.Optional[BaseException],
        tb: t.Optional[TracebackType],
    ) -> None:
        await self.client.__aexit__(typ, exc, tb)
