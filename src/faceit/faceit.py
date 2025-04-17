from __future__ import annotations

import typing as t
from abc import ABC
from warnings import warn

from ._repr import representation
from ._typing import ClientT, ResourceT, Self, ValidUUID
from .constants import BASE_WIKI_URL
from .http import AsyncClient, SyncClient
from .resources import AsyncResources, SyncResources

if t.TYPE_CHECKING:
    from types import TracebackType


@representation("client", "resources")
class BaseFaceit(t.Generic[ClientT, ResourceT], ABC):
    __slots__ = "_client", "_resources"

    _client_cls: t.Type[ClientT]
    _resources_cls: t.Type[ResourceT]

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

        self._resources = self.__class__._resources_cls(self._client)

    @property
    def client(self) -> ClientT:
        return self._client

    @property
    def resources(self) -> ResourceT:
        return self._resources

    def __str__(self) -> str:
        return (
            f"FACEIT API interface "
            f"(resources and client, docs: {BASE_WIKI_URL})"
        )


@t.final
class Faceit(BaseFaceit[SyncClient, SyncResources]):
    __slots__ = ()

    _client_cls = SyncClient
    _resources_cls = SyncResources

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
class AsyncFaceit(BaseFaceit[AsyncClient, AsyncResources]):
    __slots__ = ()

    _client_cls = AsyncClient
    _resources_cls = AsyncResources

    MAX_CONCURRENT_REQUESTS: t.ClassVar[int] = (
        AsyncClient.MAX_CONCURRENT_REQUESTS
    )

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
