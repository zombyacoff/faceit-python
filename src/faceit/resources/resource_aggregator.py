from __future__ import annotations

import typing as t
from abc import ABC
from dataclasses import dataclass
from functools import cached_property

import typing_extensions as te

from faceit.http import AsyncClient, SyncClient
from faceit.types import ClientT
from faceit.utils import noop

if t.TYPE_CHECKING:
    from types import TracebackType

_AggregatorT = t.TypeVar("_AggregatorT", bound="BaseResources")


@dataclass(eq=False, frozen=True)
class BaseResources(t.Generic[ClientT], ABC):
    __slots__ = ("_client",)

    _client: ClientT

    @property
    def client(self) -> ClientT:
        """
        The underlying HTTP client instance for low-level interactions with the
        Faceit API (e.g., unsupported endpoints or advanced use cases).

        This object provides direct access to the raw HTTP client used by the library,
        allowing you to perform custom requests to the Faceit API when the high-level
        interface does not cover your needs.

        .. note::
            For most use cases, it is recommended to use the library's standard methods.
            Access the low-level client only when interacting with non-standard or
            experimental API features.
        """
        return self._client


class SyncResources(BaseResources[SyncClient]):
    __slots__ = ()

    def __enter__(self) -> te.Self:
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
    __slots__ = ()

    def __enter__(self) -> t.NoReturn:
        self._client.__enter__()

    __exit__ = noop

    async def __aenter__(self) -> te.Self:
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        typ: t.Optional[t.Type[BaseException]],
        exc: t.Optional[BaseException],
        tb: t.Optional[TracebackType],
    ) -> None:
        await self._client.__aexit__(typ, exc, tb)


def resource_aggregator(cls: t.Type[_AggregatorT]) -> t.Type[_AggregatorT]:
    if getattr(cls, "__annotations__", None) is None:
        raise ValueError("Class must have annotations")

    for name, resource_type in cls.__annotations__.items():

        def make_property(
            is_raw: bool,
            resource_type: t.Type[t.Any] = resource_type,
        ) -> cached_property:
            return cached_property(
                lambda self: resource_type(self._client, is_raw)
            )

        prop = make_property(name.startswith("raw_"))
        setattr(cls, name, prop)
        if hasattr(prop, "__set_name__"):
            prop.__set_name__(cls, name)

    return cls
