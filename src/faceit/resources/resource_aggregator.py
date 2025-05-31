from __future__ import annotations

import typing
from abc import ABC
from dataclasses import dataclass
from functools import cached_property

from typing_extensions import Self

from faceit.http import AsyncClient, SyncClient
from faceit.types import ClientT
from faceit.utils import noop

if typing.TYPE_CHECKING:
    from types import TracebackType

_AggregatorT = typing.TypeVar("_AggregatorT", bound="BaseResources[typing.Any]")


@dataclass(eq=False, frozen=True)
class BaseResources(ABC, typing.Generic[ClientT]):
    __slots__ = ("_client",)

    _client: ClientT

    @property
    def client(self) -> ClientT:
        return self._client


class SyncResources(BaseResources[SyncClient]):
    __slots__ = ()

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

    def __enter__(self) -> typing.NoReturn:
        self._client.__enter__()

    __exit__ = noop

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
