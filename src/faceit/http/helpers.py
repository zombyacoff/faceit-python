from __future__ import annotations

import typing
from ssl import SSLError

import httpx
from typing_extensions import Self, TypeAlias

from faceit.utils import StrEnum, UnsupportedOperationTypeError, representation

if typing.TYPE_CHECKING:
    from tenacity import RetryCallState, RetryError
    from tenacity.retry import retry_base
    from tenacity.stop import stop_base
    from tenacity.wait import wait_base

    from faceit.types import EndpointParam

    _RetryHook: TypeAlias = typing.Callable[
        [RetryCallState], typing.Union[typing.Awaitable[None], None]
    ]


@typing.final
class RetryArgs(typing.TypedDict, total=False):
    sleep: typing.Callable[
        [typing.Union[int, float]], typing.Union[typing.Awaitable[None], None]
    ]
    stop: typing.Union[stop_base, typing.Callable[[RetryCallState], bool]]
    wait: typing.Union[
        wait_base, typing.Callable[[RetryCallState], typing.Union[float, int]]
    ]
    retry: typing.Union[
        retry_base,
        typing.Callable[[RetryCallState], typing.Union[typing.Awaitable[bool], bool]],
    ]
    before: _RetryHook
    after: _RetryHook
    before_sleep: typing.Optional[_RetryHook]
    reraise: bool
    retry_error_cls: typing.Type[RetryError]
    retry_error_callback: typing.Optional[typing.Callable[[RetryCallState], typing.Any]]


@typing.runtime_checkable
class SupportsExceptionPredicate(typing.Protocol):
    predicate: typing.Callable[
        [BaseException], typing.Union[typing.Awaitable[bool], bool]
    ]


class SupportedMethod(StrEnum):
    GET = "GET"
    POST = "POST"


@typing.final
@representation(use_str=True)
class Endpoint:
    __slots__ = ("base", "path_parts")

    def __init__(self, *path_parts: str, base: typing.Optional[str] = None) -> None:
        self.path_parts = list(filter(None, path_parts))
        self.base = base

    def add(self, *path_parts: str) -> Self:
        return self.__class__(*self.path_parts, *path_parts, base=self.base)

    def with_base(self, base: str) -> Self:
        return self.__class__(*self.path_parts, base=base)

    def __str__(self) -> str:
        return "/".join(
            part.strip("/") for part in [self.base, *self.path_parts] if part
        )

    def __truediv__(self, other: EndpointParam) -> Self:
        if isinstance(other, str):
            return self.add(other)
        if isinstance(other, self.__class__):
            return self.__class__(*self.path_parts, *other.path_parts, base=self.base)
        raise UnsupportedOperationTypeError(
            "/", self.__class__.__name__, type(other).__name__
        )

    def __itruediv__(self, other: EndpointParam) -> Self:
        if isinstance(other, str):
            if other:
                self.path_parts.append(other)
            return self
        if isinstance(other, self.__class__):
            self.path_parts.extend(other.path_parts)
            return self
        raise UnsupportedOperationTypeError(
            "/=", self.__class__.__name__, type(other).__name__
        )


def is_ssl_error(exception: BaseException, /) -> bool:
    return isinstance(exception, SSLError) or (
        isinstance(exception, httpx.ConnectError)
        and ("SSL" in str(exception) or "TLS" in str(exception))
    )
