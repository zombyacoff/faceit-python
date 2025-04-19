from __future__ import annotations

import typing as t

from faceit._utils import raise_unsupported_operand_error, representation

if t.TYPE_CHECKING:
    from faceit._typing import EndpointParam, Self


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
