from __future__ import annotations

import typing as t
from abc import ABC
from warnings import warn

from ._resources import AsyncDataResource, SyncDataResource
from ._typing import ClientT, DataT, ValidUUID
from ._utils import representation
from .constants import BASE_WIKI_URL
from .http import AsyncClient, SyncClient


@representation(use_str=True)
class BaseFaceit(t.Generic[ClientT, DataT], ABC):
    __slots__ = ()

    _client_cls: t.Type[ClientT]
    _data_cls: t.Type[DataT]

    def __init_subclass__(
        cls, *, client: t.Type[ClientT], data: t.Type[DataT], **kwargs: t.Any
    ) -> None:
        super().__init_subclass__(**kwargs)
        cls._client_cls = client
        cls._data_cls = data

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
        auth_param_name: str,
        client: t.Optional[ClientT] = None,
        /,
        *,
        auth: t.Optional[ValidUUID] = None,
        **client_options: t.Any,
    ) -> ClientT:
        if auth is None and client is None:
            raise ValueError(
                f"Either '{auth_param_name}' or 'client' must be provided"
            )

        if auth is not None and client is not None:
            raise ValueError(
                f"Provide either '{auth_param_name}' or 'client', not both"
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

    def __str__(self) -> str:
        return (
            f"FACEIT API interface "
            f"(Official documentation: {BASE_WIKI_URL})"
        )


@t.final
class Faceit(
    BaseFaceit[SyncClient, SyncDataResource],
    client=SyncClient,
    data=SyncDataResource,
):
    """
    Synchronous Faceit API interface.

    Example::

        from faceit import Faceit

        with Faceit.data("YOUR_API_KEY") as f:
            player = f.players.get("s1mple")
            assert player.nickname == "s1mple"
    """

    __slots__ = ()


@t.final
class AsyncFaceit(
    BaseFaceit[AsyncClient, AsyncDataResource],
    client=AsyncClient,
    data=AsyncDataResource,
):
    """
    Asynchronous Faceit API interface.

    Example::

        from faceit import AsyncFaceit

        async with AsyncFaceit.data("YOUR_API_KEY") as f:
            player = await f.players.get("s1mple")
            assert player.nickname == "s1mple"
    """

    __slots__ = ()
