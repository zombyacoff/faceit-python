from __future__ import annotations

import typing as t
from abc import ABC
from warnings import warn

from .http import AsyncClient, SyncClient
from .resources import AsyncDataResource, SyncDataResource
from .types import ClientT, DataResourceT, ValidUUID


class BaseFaceit(t.Generic[ClientT, DataResourceT], ABC):
    __slots__ = ()

    _client_cls: t.Type[ClientT]
    _data_cls: t.Type[DataResourceT]

    def __new__(cls) -> t.NoReturn:
        raise TypeError(
            f"Direct instantiation of {cls.__name__} is not allowed. "
            f"Use classmethods or factory methods instead."
        )

    @t.overload
    @classmethod
    def data(
        cls, api_key: ValidUUID, **client_options: t.Any
    ) -> DataResourceT: ...

    @t.overload
    @classmethod
    def data(cls, *, client: ClientT) -> DataResourceT: ...

    @classmethod
    def data(
        cls,
        api_key: t.Optional[ValidUUID] = None,
        *,
        client: t.Optional[ClientT] = None,
        **client_options: t.Any,
    ) -> DataResourceT:
        """
        Create and return a Faceit Data API resource.

        .. important::
            You must provide either an ``api_key`` or a pre-configured HTTP client instance — **never both**.

            - If ``api_key`` is supplied, a new HTTP client will be initialized with the given options.
            - If ``client`` is supplied, any ``client_options`` are ignored.

        Refer to the `Faceit Data API documentation <https://docs.faceit.com/docs/data-api/data>`_ and
        `API key instructions <https://docs.faceit.com/getting-started/authentication/api-keys>`_
        for details.

        :param api_key: FACEIT API key (``str``, ``UUID``, or ``bytes``). Used to create a new HTTP client.
        :param client: Pre-configured HTTP client instance. Cannot be combined with ``api_key``.
        :param client_options: Additional keyword arguments for HTTP client initialization
                            (e.g., timeouts, proxies). Ignored if ``client`` is provided.
        :return: A ready-to-use Faceit Data API resource instance.
        """
        return cls._data_cls(
            cls._initialize_client(
                api_key, client, auth_name="api_key", **client_options
            )
        )

    # TODO: The client initialization logic should be revisited when support
    # for API resources beyond Data is introduced.
    @classmethod
    def _initialize_client(
        cls,
        auth: t.Optional[ValidUUID] = None,
        client: t.Optional[ClientT] = None,
        /,
        *,
        auth_name: str,
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

    Example (Data API)::

        with Faceit.data("YOUR_API_KEY") as data:
            player = data.players.get("s1mple")
            assert player.nickname == "s1mple"

    This class uses a synchronous HTTP client under the hood.
    """

    __slots__ = ()
    _client_cls = SyncClient
    _data_cls = SyncDataResource


@t.final
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
