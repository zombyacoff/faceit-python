from __future__ import annotations

import typing as t
from abc import ABC
from dataclasses import dataclass
from functools import cached_property

from faceit._typing import ClientT, Self
from faceit.http import AsyncClient, SyncClient

from .base import BaseResource

if t.TYPE_CHECKING:
    from types import TracebackType

_RT = t.TypeVar("_RT", bound=BaseResource)
_AT = t.TypeVar("_AT", bound="BaseResources")


@dataclass(eq=False, frozen=True)
class BaseResources(t.Generic[ClientT], ABC):
    _client: ClientT

    @property
    def client(self) -> ClientT:
        """
        The underlying HTTP client instance for low-level interactions with the
        Faceit API (e.g., unsupported endpoints or advanced use cases).
        """
        return self._client


class SyncResources(BaseResources[SyncClient]):
    def __enter__(self) -> Self:
        self._client.__enter__()
        return self

    def __exit__(
        self,
        typ: t.Optional[t.Type[BaseException]],
        exc: t.Optional[BaseException],
        tb: t.Optional[TracebackType],
    ) -> None:
        self._client.__exit__(typ, exc, tb)


class AsyncResources(BaseResources[AsyncClient]):
    async def __aenter__(self) -> Self:
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        typ: t.Optional[t.Type[BaseException]],
        exc: t.Optional[BaseException],
        tb: t.Optional[TracebackType],
    ) -> None:
        await self._client.__aexit__(typ, exc, tb)


def resource_aggregator(cls: t.Type[_AT]) -> t.Type[_AT]:
    if getattr(cls, "__annotations__", None) is None:
        raise ValueError("Class must have annotations")

    for name, resource_type in cls.__annotations__.items():

        def make_property(
            is_raw: bool,
            resource_type: t.Type[_RT] = resource_type,
        ) -> cached_property:
            return cached_property(
                lambda self: resource_type(self._client, raw=is_raw)
            )

        prop = make_property(name.startswith("raw_"))
        setattr(cls, name, prop)
        if hasattr(prop, "__set_name__"):
            prop.__set_name__(cls, name)

    return cls
