from __future__ import annotations

import hashlib
import json
import typing as t
from datetime import datetime, timezone
from enum import IntEnum
from functools import lru_cache, reduce
from uuid import UUID

if t.TYPE_CHECKING:
    from ._typing import ParamSpec

    _T = t.TypeVar("_T")
    _P = ParamSpec("_P")

# NOTE: While similar utility functions likely exist in third-party libraries,
# we've chosen to implement them directly to minimize external dependencies
# This approach reduces project complexity and potential version conflicts
# while maintaining full control over the implementation details


class UnsetValue(IntEnum):
    UNSET = -1


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


def get_hashable_representation(obj: t.Any, /) -> int:
    try:
        return hash(obj)
    except TypeError:
        try:
            return int.from_bytes(
                hashlib.sha256(
                    json.dumps(obj, sort_keys=True, default=str).encode()
                ).digest()[:8],
                "big",
                signed=True,
            )
        except (TypeError, ValueError):
            # For objects that can't be JSON serialized,
            # use their string representation
            # This is less precise but safer than pickle
            return hash(str(obj))


# NOTE: Some API methods return Unix timestamps in milliseconds


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


# We maintain our own `UUID` validation implementation despite potentially more
# efficient alternatives. This specific implementation is crucial for the
# library's internal logic to distinguish between different resource types
# (e.g., nickname vs ID) and supports the expected behavior of various
# resource handlers

_UUID_BYTES: t.Final = 16


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
