from __future__ import annotations

import typing
from abc import ABC
from functools import cached_property
from warnings import warn

from typing_extensions import Self

from faceit.http import AsyncClient, EnvKey, SyncClient
from faceit.types import ClientT, ValidUUID
from faceit.utils import NullCallable

if typing.TYPE_CHECKING:
    from types import TracebackType

    from faceit.http.client import BaseAPIClient

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
            raise ValueError(f"Provide either {secret_type!r} or 'client', not both")

        if client is None:
            self._client = self._client_cls(
                EnvKey(f"FACEIT_{secret_type.upper()}") if auth is None else auth,
                **client_options,
            )
            return

        if client_options:
            warn(
                "'client_options' are ignored when an existing client "
                "instance is provided. Configure your client before "
                "passing it to this constructor.",
                UserWarning,
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

    def __exit__(
        self,
        typ: typing.Optional[typing.Type[BaseException]],
        exc: typing.Optional[BaseException],
        tb: typing.Optional[TracebackType],
    ) -> None:
        self._client.__exit__(typ, exc, tb)


class AsyncResources(BaseResources[AsyncClient]):
    __slots__ = ()

    _client_cls = AsyncClient

    def __enter__(self) -> typing.NoReturn:
        self._client.__enter__()

    __exit__ = NullCallable()

    async def __aenter__(self) -> Self:
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        typ: typing.Optional[typing.Type[BaseException]],
        exc: typing.Optional[BaseException],
        tb: typing.Optional[TracebackType],
    ) -> None:
        await self._client.__aexit__(typ, exc, tb)


def resource_aggregator(cls: typing.Type[_AggregatorT], /) -> typing.Type[_AggregatorT]:
    for name, resource_type in cls.__annotations__.items():

        def make_property(
            is_raw: bool,
            resource_type: typing.Type[typing.Any] = resource_type,
        ) -> cached_property[_AggregatorT]:
            return cached_property(lambda self: resource_type(self._client, is_raw))

        prop = make_property(name.startswith("raw_"))
        setattr(cls, name, prop)
        prop.__set_name__(cls, name)

    return cls
