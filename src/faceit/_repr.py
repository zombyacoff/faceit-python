from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from ._typing import TypeAlias

_ReprMethod: TypeAlias = t.Callable[[], str]
_ClassT = t.TypeVar("_ClassT", bound=t.Type)

_UNINITIALIZED_MARKER: t.Final = "uninitialized"


def _format_fields(
    obj: t.Any, fields: t.Tuple[str, ...], joiner: str = " ", /
) -> str:
    return (
        joiner.join(f"{field}={getattr(obj, field)!r}" for field in fields)
        if all(hasattr(obj, field) for field in fields)
        else repr(_UNINITIALIZED_MARKER)
    )


def _apply_representation(
    cls: _ClassT, fields: t.Tuple[str, ...], use_str: bool, /
) -> _ClassT:
    has_str = getattr(cls, "__str__", None) is not object.__str__

    if use_str and not has_str:
        raise TypeError(f"Class {cls.__name__} must define __str__ method")

    def repr_(self: _ClassT) -> str:
        str_args = (
            f"'{self}'" if use_str else _format_fields(self, fields, ", ")
        )
        return f"{cls.__name__}({str_args})"

    def str_(self: _ClassT) -> str:
        return _format_fields(self, fields)

    cls.__repr__ = t.cast(_ReprMethod, repr_)
    if not has_str:
        cls.__str__ = t.cast(_ReprMethod, str_)

    return cls


def representation(
    *fields: str, use_str: bool = False
) -> t.Callable[[_ClassT], _ClassT]:
    def decorator(cls: _ClassT) -> _ClassT:
        return _apply_representation(cls, fields, use_str)

    return decorator
