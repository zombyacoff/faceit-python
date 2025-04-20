from __future__ import annotations

import json
import reprlib
import typing as t
from contextlib import suppress
from datetime import datetime, timezone
from enum import IntEnum
from functools import lru_cache, reduce
from hashlib import sha256
from uuid import UUID

from strenum import StrEnum

if t.TYPE_CHECKING:
    from ._typing import Self, TypeAlias

    _T = t.TypeVar("_T")
    _ClassT = t.TypeVar("_ClassT", bound=t.Type)

_ReprMethod: TypeAlias = t.Callable[[], str]

_UUID_BYTES: t.Final = 16
_UNINITIALIZED_MARKER: t.Final = "uninitialized"


class UnsetValue(IntEnum):
    UNSET = -1


class StrEnumWithAll(StrEnum):
    @classmethod
    def all(cls) -> t.Tuple[Self, ...]:
        return tuple(cls)


def lazy_import(func: t.Callable[[], _T]) -> t.Callable[[], _T]:
    return lru_cache(maxsize=1)(func)


def raise_unsupported_operand_error(
    sign: str,
    self_name: str,
    other_name: str,
    /,
) -> t.NoReturn:
    raise TypeError(
        f"unsupported operand type(s) for {sign}: "
        f"'{self_name}' and '{other_name}'"
    )


def deep_get(
    dictionary: t.Dict[str, t.Any],
    keys: str,
    /,
    default: t.Optional[_T] = None,
) -> t.Union[_T, t.Any]:
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
        keys.split("."),
        dictionary,
    )


def get_nested_property(
    obj: t.Any, path: str, /, default: t.Optional[_T] = None
) -> t.Union[_T, t.Any]:
    if obj is None or not path:
        return default
    try:
        return reduce(
            lambda o, k: getattr(o, k) if o is not None else default,
            path.split("."),
            obj,
        )
    except (AttributeError, TypeError):
        return default


def _fallback_hash(obj: str, /) -> int:
    return int.from_bytes(
        sha256(obj.encode()).digest()[:8], "big", signed=True
    )


def _get_hashable_representation(obj: t.Any, /) -> int:
    with suppress(TypeError):
        return hash(obj)
    try:
        obj_str = json.dumps(obj, sort_keys=True, default=str)
    except (TypeError, AttributeError):
        obj_str = str(obj)
    return _fallback_hash(obj_str)


def deduplicate_unhashable(values: t.Iterable[_T], /) -> t.List[_T]:
    return list(
        {_get_hashable_representation(item): item for item in values}.values()
    )


def to_unix(
    value: t.Optional[datetime], /, *, millis: bool = False
) -> t.Optional[int]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return int(value.timestamp()) * (1000 if millis else 1)
    raise ValueError(f"Expected datetime or None, got {type(value).__name__}")


def from_unix(
    value: t.Optional[int], /, *, millis: bool = False
) -> t.Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, int):
        return datetime.fromtimestamp(
            value / (1000 if millis else 1), tz=timezone.utc
        )
    raise ValueError(f"Expected int or None, got {type(value).__name__}")


def to_uuid(value: t.Union[str, bytes], /) -> UUID:
    if isinstance(value, str):
        return UUID(value)
    if not isinstance(value, bytes):
        raise TypeError("Expected str or bytes for UUID conversion")
    try:
        return UUID(value.decode())
    except UnicodeDecodeError as e:
        if len(value) == _UUID_BYTES:
            return UUID(bytes=value)
        raise ValueError(
            f"Byte value must be a UTF-8 encoded "
            f"UUID string or {_UUID_BYTES} bytes"
        ) from e


def is_valid_uuid(value: t.Any, /) -> bool:
    if isinstance(value, UUID):
        return True
    if not isinstance(value, (str, bytes)):
        return False
    try:
        to_uuid(value)
    except (AttributeError, ValueError):
        return False
    return True


def create_uuid_validator(
    error_message: str = "Invalid {arg_name}: {value}. Expected a valid UUID.",
    /,
    *,
    arg_name: str = "value",
) -> t.Callable[[t.Any], str]:
    def validator(value: t.Any, /) -> str:
        if not is_valid_uuid(value):
            raise ValueError(
                error_message.format(arg_name=arg_name, value=value)
            )
        if isinstance(value, (UUID, str)):
            return str(value)
        assert isinstance(value, bytes)  # noqa: S101
        return str(to_uuid(value))

    return validator


def _format_fields(
    obj: t.Any, fields: t.Tuple[str, ...], joiner: str = " ", /
) -> str:
    return (
        joiner.join(
            f"{field}={reprlib.repr(getattr(obj, field))}" for field in fields
        )
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
        return f"{self.__class__.__name__}({str_args})"

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
