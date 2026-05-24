from __future__ import annotations

from ssl import SSLError
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    TypeAlias,
    TypedDict,
    final,
    runtime_checkable,
)

import httpx
from typing_extensions import Self

from faceit.utils import representation

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    import tenacity

    from faceit.types import EndpointLike

    _RetryHook: TypeAlias = Callable[[tenacity.RetryCallState], Awaitable[None] | None]


@final
class RetryArgs(TypedDict, total=False):
    sleep: Callable[[int | float], Awaitable[None] | None]
    stop: tenacity.stop.stop_base | Callable[[tenacity.RetryCallState], bool]
    wait: tenacity.wait.wait_base | Callable[[tenacity.RetryCallState], float | int]
    retry: (
        tenacity.retry_base
        | Callable[[tenacity.RetryCallState], Awaitable[bool] | bool]
    )
    before: _RetryHook
    after: _RetryHook
    before_sleep: _RetryHook | None
    reraise: bool
    retry_error_cls: type[tenacity.RetryError]
    retry_error_callback: Callable[[tenacity.RetryCallState], Any] | None


@runtime_checkable
class SupportsExceptionPredicate(Protocol):
    predicate: Callable[[BaseException], Awaitable[bool] | bool]


@final
@representation(use_str=True)
class Endpoint:
    __slots__ = ("base", "path_parts")

    def __init__(self, *path_parts: str, base: str | None = None) -> None:
        self.path_parts = list(filter(None, path_parts))
        self.base = base

    def add(self, *path_parts: str) -> Self:
        return self.__class__(*self.path_parts, *path_parts, base=self.base)

    def with_base(self, base: str, /) -> Self:
        return self.__class__(*self.path_parts, base=base)

    def __str__(self) -> str:
        return "/".join(
            part.strip("/") for part in [self.base, *self.path_parts] if part
        )

    def __truediv__(self, other: EndpointLike) -> Self:
        if not isinstance(other, self.__class__):
            return self.add(str(other))
        return self.__class__(*self.path_parts, *other.path_parts, base=self.base)

    def __itruediv__(self, other: EndpointLike) -> Self:
        if isinstance(other, self.__class__):
            self.path_parts.extend(other.path_parts)
            return self
        other_str = str(other)
        if other_str:
            self.path_parts.append(other_str)
        return self


def is_ssl_error(exception: BaseException, /) -> bool:
    return isinstance(exception, SSLError) or (
        isinstance(exception, httpx.ConnectError)
        and ("SSL" in str(exception) or "TLS" in str(exception))
    )


def is_retryable_status(code: int, /) -> bool:
    return code == httpx.codes.TOO_MANY_REQUESTS or httpx.codes.is_server_error(code)
