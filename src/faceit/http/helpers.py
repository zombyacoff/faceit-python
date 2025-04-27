from __future__ import annotations

import typing as t
from enum import auto

from faceit.utils import (
    StrEnum,
    raise_unsupported_operand_error,
    representation,
)

if t.TYPE_CHECKING:
    from tenacity import RetryCallState, RetryError
    from tenacity.asyncio.retry import async_retry_base
    from tenacity.retry import retry_base
    from tenacity.stop import stop_base
    from tenacity.wait import wait_base

    from faceit.types import EndpointParam, Self, TypeAlias

    _StopBase: TypeAlias = t.Union[
        stop_base, t.Callable[[RetryCallState], bool]
    ]
    _WaitBase: TypeAlias = t.Union[
        wait_base, t.Callable[[RetryCallState], t.Union[float, int]]
    ]
    _RetryHook: TypeAlias = t.Callable[
        [RetryCallState], t.Union[None, t.Awaitable[None]]
    ]


@t.final
class RetryArgs(t.TypedDict, total=False):
    sleep: t.Callable[[t.Union[int, float]], t.Union[None, t.Awaitable[None]]]
    stop: _StopBase
    wait: _WaitBase
    retry: t.Union[
        retry_base,
        async_retry_base,
        t.Callable[[RetryCallState], t.Union[bool, t.Awaitable[bool]]],
    ]
    before: _RetryHook
    after: _RetryHook
    before_sleep: t.Optional[_RetryHook]
    reraise: bool
    retry_error_cls: t.Type[RetryError]
    retry_error_callback: t.Optional[t.Callable[[RetryCallState], t.Any]]


class SupportedMethod(StrEnum):
    GET = auto()
    POST = auto()


@t.final
@representation(use_str=True)
class Endpoint:
    __slots__ = ("base_path", "path_parts")

    def __init__(
        self, *path_parts: str, base_path: t.Optional[str] = None
    ) -> None:
        self.path_parts = list(filter(None, path_parts))
        self.base_path = base_path

    def __str__(self) -> str:
        parts = ([self.base_path] if self.base_path else []) + self.path_parts
        return "/".join(part.strip("/") for part in parts if part)

    def add(self, *path_parts: str) -> Self:
        return self.__class__(
            *self.path_parts, *path_parts, base_path=self.base_path
        )

    def with_base(self, base_path: str) -> Self:
        return self.__class__(*self.path_parts, base_path=base_path)

    def __truediv__(self, other: EndpointParam) -> Self:
        if isinstance(other, str):
            return self.add(other)
        if isinstance(other, self.__class__):
            return self.__class__(
                *self.path_parts, *other.path_parts, base_path=self.base_path
            )
        # Intentional error path - Ruff limitation (RET503)
        raise_unsupported_operand_error(  # noqa: RET503
            "/", self.__class__.__name__, type(other).__name__
        )

    # Ruff cannot detect that we already use `Self` here (PYI034),
    # likely because it's imported indirectly via a re-exporting module,
    # not directly from `typing`/`typing_extensions`.
    def __itruediv__(self, other: EndpointParam) -> Self:  # noqa: PYI034
        if isinstance(other, str):
            if other:
                self.path_parts.append(other)
            return self
        if isinstance(other, self.__class__):
            self.path_parts.extend(other.path_parts)
            return self
        raise_unsupported_operand_error(  # noqa: RET503
            "/=", self.__class__.__name__, type(other).__name__
        )
