from __future__ import annotations

import typing
import warnings
from abc import ABC
from functools import cached_property

from typing_extensions import Never, Self

from faceit.http import AsyncClient, FromEnv, SyncClient
from faceit.types import ClientT, Raw, ValidUUID

if typing.TYPE_CHECKING:
    from faceit.api.base import BaseResource
    from faceit.http.client import BaseAPIClient

    _ResourceT = typing.TypeVar("_ResourceT", bound="BaseResource[typing.Any]")
    _AggregatorT = typing.TypeVar("_AggregatorT", bound="BaseResources[typing.Any]")


class BaseResources(ABC, typing.Generic[ClientT]):
    __slots__ = ("_client",)

    if typing.TYPE_CHECKING:
        _client: ClientT
        _client_cls: typing.Type[ClientT]

    def _initialize_client(
        self,
        auth: typing.Union[ValidUUID, BaseAPIClient.env, None] = None,
        client: typing.Optional[ClientT] = None,
        /,
        *,
        secret_type: str,
        **client_options: typing.Any,
    ) -> None:
        if auth is not None and client is not None:
            msg = f"Provide either {secret_type!r} or 'client', not both"
            raise ValueError(msg)

        if client is None:
            key = FromEnv(f"FACEIT_{secret_type.upper()}") if auth is None else auth
            self._client = self._client_cls(key, **client_options)
            return

        if client_options:
            warnings.warn(
                "'client_options' are ignored when an existing client "
                "instance is provided. Configure your client before "
                "passing it to this constructor.",
                stacklevel=3,
            )

        self._client = client
        return

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


def resource_aggregator(cls: typing.Type[_AggregatorT], /) -> typing.Type[_AggregatorT]:
    for name, resource_type in cls.__annotations__.items():

        def make_property(
            resource_type: typing.Type[_ResourceT], *, is_raw: bool
        ) -> cached_property[_ResourceT]:
            def factory(self: _AggregatorT) -> _ResourceT:
                return resource_type(self._client, raw=is_raw)

            return cached_property(factory)

        property_ = make_property(
            resource_type,
            is_raw=Raw in typing.get_args(resource_type),
        )
        setattr(cls, name, property_)
        property_.__set_name__(cls, name)

    return cls
