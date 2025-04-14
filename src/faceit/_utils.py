from __future__ import annotations

import hashlib
import json
import typing as t
from datetime import datetime, timezone
from functools import lru_cache, reduce, wraps
from inspect import signature
from uuid import UUID

if t.TYPE_CHECKING:
    from ._types import ParamSpec

    _T = t.TypeVar("_T")
    _P = ParamSpec("_P")

# NOTE: While similar utility functions likely exist in third-party libraries,
# we've chosen to implement them directly to minimize external dependencies
# This approach reduces project complexity and potential version conflicts
# while maintaining full control over the implementation details


def lazy_import(func: t.Callable[[], _T]) -> t.Callable[[], _T]:
    """Decorator for lazy importing to prevent cyclic dependencies.

    This is an alias for `lru_cache(maxsize=1)` with a more descriptive name.
    """
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


def convert_to_unix(
    value: t.Optional[datetime], /, *, millis: bool = False
) -> t.Optional[int]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return int(value.timestamp()) * (1000 if millis else 1)
    raise ValueError(f"Expected datetime or None, got {type(value).__name__}")


def convert_from_unix(
    value: t.Optional[int], /, *, millis: bool = False
) -> t.Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, int):
        return datetime.fromtimestamp(
            value / (1000 if millis else 1), tz=timezone.utc
        )
    raise ValueError(f"Expected int or None, got {type(value).__name__}")


# We maintain our own `UUID` validation implementation despite potentially more efficient
# alternatives. This specific implementation is crucial for the library's internal logic to
# distinguish between different resource types (e.g., nickname vs ID) and supports the
# expected behavior of various resource handlers
def is_valid_uuid(value: t.Any, /) -> bool:
    if isinstance(value, UUID):
        return True
    if not isinstance(value, (str, bytes)):
        return False
    try:
        UUID(value if isinstance(value, str) else value.decode())
    except (ValueError, AttributeError):
        return False
    return True


def validate_uuid_args(
    *arg_names: str, error_message: t.Optional[str] = None
) -> t.Callable[[t.Callable[_P, _T]], t.Callable[_P, _T]]:
    def decorator(func: t.Callable[_P, _T]) -> t.Callable[_P, _T]:
        sig = signature(func)

        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            bound_args = sig.bind(*args, **kwargs).arguments

            for arg_name in arg_names:
                if arg_name not in bound_args:
                    continue

                value = bound_args[arg_name]

                if value is None:
                    continue

                if not is_valid_uuid(value):
                    raise ValueError(
                        error_message
                        or f"Invalid {arg_name}: {value}. Must be a valid UUID."
                    )

            return func(*args, **kwargs)

        return wrapper

    return decorator
