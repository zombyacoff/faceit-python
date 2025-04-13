from __future__ import annotations

import typing as t

from faceit import _repr

if t.TYPE_CHECKING:
    from faceit._types import EndpointParam, Self


@t.final
@_repr.representation(use_str=True)
class Endpoint:
    __slots__ = "base_path", "path_parts"

    def __init__(
        self, *path_parts: str, base_path: t.Optional[str] = None
    ) -> None:
        self.path_parts = list(filter(None, path_parts))
        self.base_path = base_path

    def __str__(self) -> str:
        all_parts = (
            [self.base_path] if self.base_path else []
        ) + self.path_parts
        return "/".join(part.strip("/") for part in all_parts if part)

    def __truediv__(self, other: EndpointParam) -> Self:
        if isinstance(other, str):
            return self.add(other)
        if isinstance(other, self.__class__):
            return self.__class__(
                *self.path_parts, *other.path_parts, base_path=self.base_path
            )
        raise TypeError(
            f"unsupported operand type(s) for /: "
            f"'{self.__class__.__name__}' and '{type(other).__name__}'"
        )

    def add(self, *path_parts: str) -> Self:
        return self.__class__(
            *self.path_parts, *path_parts, base_path=self.base_path
        )

    def with_base(self, base_path: str) -> Self:
        return self.__class__(*self.path_parts, base_path=base_path)
