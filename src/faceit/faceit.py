import warnings
from abc import ABC
from typing import Any, Final, Generic, Optional, Type, final, overload

from .constants import BASE_WIKI_URL
from .http import AsyncClient, SyncClient
from .resources import AsyncResources, SyncResources
from .types import ClientT, ResourceT, Self


class BaseFaceit(Generic[ClientT, ResourceT], ABC):
    __slots__ = "_client", "_resources"

    _client_cls: Type[ClientT]
    _resources_cls: Type[ResourceT]

    WIKI_URL: Final = BASE_WIKI_URL
    """URL to the official FACEIT API documentation."""

    @overload
    def __init__(self, *, api_key: str, **client_kwargs: Any) -> None: ...
    @overload
    def __init__(self, *, client: ClientT) -> None: ...
    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[ClientT] = None,
        **client_kwargs: Any,
    ) -> None:
        """Initialize a FACEIT API interface.

        This constructor provides two ways to initialize the interface:
        1. By providing an API key, which will create a new client instance
        2. By providing an existing client instance

        Args:
            api_key: Your FACEIT API key for authentication. Required if `client` is not provided.
                     Can be obtained from the FACEIT Developer Portal.
            client: An existing client instance (either `SyncClient` or `AsyncClient`).
                    Required if `api_key` is not provided.
            **client_kwargs: Additional keyword arguments to pass to the client constructor.
                             These are ignored if `client` is provided.

        Raises:
            ValueError: If neither `api_key` nor `client` is provided, or if both are provided.

        Examples:
            Creating with an API key:
            >>> faceit = Faceit(api_key="your-api-key-here")

            Creating with an existing client:
            >>> client = SyncClient("your-api-key-here")
            >>> faceit = Faceit(client=client)

            Creating with additional client configuration:
            >>> faceit = Faceit(
            ...     api_key="your-api-key-here",
            ...     timeout=30.0,
            ...     base_url="https://new-faceit-api.com",
            ... )
        """
        if api_key is None and client is None:
            raise ValueError("Either 'api_key' or 'client' must be provided")
        if api_key is not None and client is not None:
            raise ValueError("Provide either 'api_key' or 'client', not both")

        if client is not None:
            if client_kwargs:
                # fmt: off
                warnings.warn(
                    "'client_kwargs' are ignored when an existing client instance is provided. "
                    "Configure your client before passing it to this constructor.", UserWarning, stacklevel=2,
                )
                # fmt: on
            self._client = client
        else:
            self._client = self.__class__._client_cls(api_key, **client_kwargs)

        self._resources = self.__class__._resources_cls(self._client)

    @property
    def client(self) -> ClientT:
        """The HTTP client used to make requests to the FACEIT API.

        Example:
            >>> faceit.client.get("players/s1mple")
            {'player_id': 'ac71ba3c-d3d4-45e7-8be2-26aa3986867d', 'nickname': 's1mple', ...}
        """
        return self._client

    @property
    def resources(self) -> ResourceT:
        """The resource manager for the FACEIT API.

        Provides convenient access to API resources through dedicated methods.

        Example:
            >>> faceit.resources.players.get("s1mple")
            Player(id=FaceitUUID('ac71ba3c-d3d4-45e7-8be2-26aa3986867d'), nickname='s1mple', ...)
        """
        return self._resources

    def __str__(self) -> str:
        return f"FACEIT API interface (resources and client, docs: {self.__class__.WIKI_URL})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(client={self._client!r}, resources={self._resources.__class__.__name__})"


@final
class Faceit(BaseFaceit[SyncClient, SyncResources]):
    __slots__ = ()

    _client_cls = SyncClient
    _resources_cls = SyncResources

    def __enter__(self) -> Self:
        self.client.__enter__()
        return self

    def __exit__(self, *args, **kwargs) -> None:
        self.client.__exit__(*args, **kwargs)


@final
class AsyncFaceit(BaseFaceit[AsyncClient, AsyncResources]):
    __slots__ = ()

    _client_cls = AsyncClient
    _resources_cls = AsyncResources

    async def __aenter__(self) -> Self:
        await self.client.__aenter__()
        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.client.__aexit__(*args, **kwargs)
