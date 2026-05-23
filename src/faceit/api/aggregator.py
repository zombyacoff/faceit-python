from __future__ import annotations

from abc import ABC
from functools import cached_property
from typing import TYPE_CHECKING, Any, Generic, TypeVar, get_args

from typing_extensions import Never, Self

from faceit.http import AsyncClient, FromEnv, SyncClient
from faceit.types import ClientT, Raw, ValidUUID

if TYPE_CHECKING:
    from faceit.api.base import BaseResource
    from faceit.http.client import BaseAPIClient

    _ResourceT = TypeVar("_ResourceT", bound="BaseResource[Any]")
    _AggregatorT = TypeVar("_AggregatorT", bound="BaseResources[Any]")


class BaseResources(ABC, Generic[ClientT]):
    __slots__ = ("_client",)

    if TYPE_CHECKING:
        _client: ClientT
        _client_cls: type[ClientT]

    def _initialize_client(
        self,
        auth: ValidUUID | BaseAPIClient.env | None = None,
        client: ClientT | None = None,
        /,
        *,
        secret_type: str,
    ) -> None:
        if auth is not None and client is not None:
            msg = f"Provide either {secret_type!r} or 'client', not both"
            raise ValueError(msg)
        self._client = (
            self._client_cls(
                FromEnv(f"FACEIT_{secret_type.upper()}") if auth is None else auth
            )
            if client is None
            else client
        )

    @property
    def client(self) -> ClientT:
        return self._client


class SyncResources(BaseResources[SyncClient]):
    __slots__ = ()

    _client_cls = SyncClient

    def __enter__(self) -> Self:
        self._client.__enter__()
        return self

    def __exit__(self, *args: object, **kwargs: object) -> None:
        self._client.__exit__(*args, **kwargs)


class AsyncResources(BaseResources[AsyncClient]):
    __slots__ = ()

    _client_cls = AsyncClient

    def __enter__(self) -> Never:
        self._client.__enter__()

    __exit__ = AsyncClient.__exit__

    async def __aenter__(self) -> Self:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *args: object, **kwargs: object) -> None:
        await self._client.__aexit__(*args, **kwargs)


def resource_aggregator(cls: type[_AggregatorT], /) -> type[_AggregatorT]:
    for name, resource_type in cls.__annotations__.items():

        def make_property(
            resource_type: type[_ResourceT], *, is_raw: bool
        ) -> cached_property[_ResourceT]:
            def factory(self: _AggregatorT) -> _ResourceT:
                return resource_type(self._client, raw=is_raw)

            return cached_property(factory)

        property_ = make_property(resource_type, is_raw=Raw in get_args(resource_type))
        setattr(cls, name, property_)
        property_.__set_name__(cls, name)

    return cls
