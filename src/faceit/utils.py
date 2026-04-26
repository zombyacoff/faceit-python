from __future__ import annotations

import inspect
import json
import os
import reprlib
import sys
import typing
from contextlib import suppress
from datetime import datetime, timezone
from enum import Enum, IntEnum, auto
from functools import lru_cache, reduce, wraps
from hashlib import sha256
from uuid import UUID

from typing_extensions import Self, TypeIs

if typing.TYPE_CHECKING:
    from asyncio import Lock as AsyncLock  # noqa: ICN003
    from threading import Lock as SyncLock
    from types import FrameType

    from .types import _P, _T, ValidUUID

    _CallableT = typing.TypeVar("_CallableT", bound=typing.Callable[..., typing.Any])
    _ClassT = typing.TypeVar("_ClassT", bound=type)

_IGNORED_MODULES: typing.Set[str] = {
    "pydantic",
}
_UUID_BYTES: typing.Final = 16
_UNINITIALIZED_MARKER: typing.Final = "uninitialized"


class UnsetValue(IntEnum):
    UNSET = -1


# NOTE: Inspired by irgeek/StrEnum:
# https://github.com/irgeek/StrEnum/blob/master/strenum/__init__.py#L21
# Previously depended on `StrEnum`, but only core features were needed -
# now implemented inline to avoid extra dependencies.
class StrEnum(str, Enum):
    _value_: str

    def __new__(
        cls, value: typing.Union[str, auto], *args: object, **kwargs: object
    ) -> Self:
        if isinstance(value, (str, auto)):
            return super().__new__(cls, value, *args, **kwargs)
        raise TypeError(
            "StrEnum values must be of type 'str', "
            f"but got {type(value).__name__}: {value!r}"
        )

    @staticmethod
    def _generate_next_value_(name: str, *_: object) -> str:
        return name

    def __str__(self) -> str:
        return str(self.value)


class StrEnumWithAll(StrEnum):
    @classmethod
    def get_all_values(cls) -> typing.Tuple[Self, ...]:
        return tuple(cls)

    all = get_all_values  # alias for backwards compatibility


def UnsupportedOperationTypeError(  # noqa: N802
    sign: str, self_name: str, other_name: str
) -> TypeError:
    return TypeError(
        f"unsupported operand type(s) for {sign}: {self_name!r} and {other_name!r}"
    )


def locked(
    lock: typing.Union[SyncLock, AsyncLock], /
) -> typing.Callable[[typing.Callable[_P, _T]], typing.Callable[_P, _T]]:
    def decorator(func: typing.Callable[_P, _T], /) -> typing.Callable[_P, _T]:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
                async with typing.cast("AsyncLock", lock):  # Developer's responsibility
                    return typing.cast("_T", await func(*args, **kwargs))

            return typing.cast("typing.Callable[_P, _T]", async_wrapper)

        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            with typing.cast("SyncLock", lock):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def extends(
    _: _CallableT, /
) -> typing.Callable[[typing.Callable[..., object]], _CallableT]:
    """
    Decorator that assigns the type signature of the given function to the
    decorated function. Type checking is enforced only at the function boundary
    (when calling the function), not within the function body.
    """
    return lambda x: typing.cast("_CallableT", x)


async def invoke_callable(
    func: typing.Callable[..., typing.Union[_T, typing.Awaitable[_T]]],
    /,
    *args: typing.Any,
    **kwargs: typing.Any,
) -> _T:
    if not callable(func):
        raise TypeError(
            f"Expected a callable object, got {type(func).__name__} ({func!r}). "
            "Argument 'func' must be a function or object with a __call__ method."
        )
    result = func(*args, **kwargs)
    if inspect.isawaitable(result):
        result = await result
    return typing.cast("_T", result)


def deep_get(
    dictionary: typing.Mapping[str, typing.Any],
    keys: str,
    /,
    default: typing.Optional[_T] = None,
) -> typing.Union[_T, typing.Any, None]:
    current = dictionary
    try:
        for key in keys.split("."):
            current = current[key]
    except (KeyError, TypeError, AttributeError):
        return default
    return current


def get_nested_property(
    obj: typing.Any, path: str, /, default: typing.Optional[_T] = None
) -> typing.Union[_T, typing.Any, None]:
    if obj is None or not path:
        return default
    try:
        return reduce(
            lambda o, k: default if o is None else getattr(o, k), path.split("."), obj
        )
    except (AttributeError, TypeError):
        return default


def get_hashable_representation(obj: typing.Any, /) -> int:
    with suppress(TypeError):
        return hash(obj)
    try:
        obj_str = json.dumps(obj, default=str, sort_keys=True)
    except (TypeError, AttributeError):
        obj_str = str(obj)
    return int.from_bytes(sha256(obj_str.encode()).digest()[:8], "big", signed=True)


def deduplicate_unhashable(values: typing.Iterable[_T], /) -> typing.List[_T]:
    return list({get_hashable_representation(v): v for v in values}.values())


def to_unix(
    value: typing.Optional[datetime], /, *, millis: bool = False
) -> typing.Optional[int]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return int(value.timestamp() * (1000 if millis else 1))
    raise ValueError(f"Expected datetime or None, got {type(value).__name__}")


def from_unix(
    value: typing.Optional[float], /, *, millis: bool = False
) -> typing.Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / (1000 if millis else 1), tz=timezone.utc)
    raise ValueError(f"Expected int, float or None, got {type(value).__name__}")


def to_uuid(value: typing.Union[str, bytes], /) -> UUID:
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
            f"Byte value must be a UTF-8 encoded UUID string or {_UUID_BYTES} bytes"
        ) from e


def is_valid_uuid(value: typing.Any, /) -> TypeIs[ValidUUID]:
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
    arg_name: str = "value",
) -> typing.Callable[[typing.Any], str]:
    def validator(value: typing.Any, /) -> str:
        if is_valid_uuid(value):
            return str(value if isinstance(value, (UUID, str)) else to_uuid(value))
        raise ValueError(error_message.format(arg_name=arg_name, value=value))

    return validator


def validate_positive_int(value: typing.Any, /, param_name: str = "value") -> int:
    """
    Utility for validating that a value is a positive integer.
    Use this when :class:`pydantic.PositiveInt` type or validation is
    impractical or unavailable.
    """
    if not isinstance(value, int):
        raise TypeError(f"'{param_name}' must be int, got {type(value).__name__}")
    if value <= 0:
        raise ValueError(f"'{param_name}' must be a positive integer, got {value}")
    return value


@lru_cache(maxsize=1)
def _get_ignored_paths() -> typing.Tuple[
    typing.Tuple[str, ...],
    typing.FrozenSet[str],
]:
    prefixes: typing.List[str] = []
    files: typing.Set[str] = set()

    for mod_name in (__name__.split(".")[0], *_IGNORED_MODULES):
        mod = sys.modules.get(mod_name)
        if mod is None or not hasattr(mod, "__file__") or mod.__file__ is None:
            continue

        path = os.path.normcase(os.path.realpath(mod.__file__))

        if path.endswith("__init__.py"):
            dir_path = os.path.dirname(path) + os.sep  # noqa: PTH120
            prefixes.append(dir_path)
        else:
            files.add(path)

    return tuple(prefixes), frozenset(files)


def warn_stacklevel() -> int:
    """
    Determines the appropriate stack level for warnings emitted by the library,
    so that they point to the user's code instead of internal library frames.
    """
    with suppress(ValueError, AttributeError):
        ignored_prefixes, ignored_files = _get_ignored_paths()
        frame: typing.Optional[FrameType] = sys._getframe(1)
        level = 1

        while frame:
            filename = frame.f_code.co_filename
            if filename and not filename.startswith("<"):
                norm_path = os.path.normcase(os.path.realpath(filename))
                is_user_code = (
                    norm_path not in ignored_files
                    and not norm_path.startswith(ignored_prefixes)
                )
                if is_user_code:
                    return level

            frame = frame.f_back
            level += 1

    return 1


def _format_fields(obj: object, fields: typing.Tuple[str, ...], *, joiner: str) -> str:
    return (
        joiner.join(f"{field}={reprlib.repr(getattr(obj, field))}" for field in fields)
        if all(hasattr(obj, field) for field in fields)
        else repr(_UNINITIALIZED_MARKER)
    )


def _apply_representation(
    cls: _ClassT, fields: typing.Tuple[str, ...], use_str: bool
) -> _ClassT:
    has_str = getattr(cls, "__str__", object.__str__) is not object.__str__

    if use_str and not has_str:
        raise TypeError(
            f"Class {cls.__name__} must define '__str__' method when 'use_str=True'"
        )

    def build_repr(self: _ClassT) -> str:
        str_args = f"'{self}'" if use_str else _format_fields(self, fields, joiner=", ")
        return f"{self.__class__.__name__}({str_args})"

    def build_str(self: _ClassT) -> str:
        return _format_fields(self, fields, joiner=" ")

    cls.__repr__ = build_repr  # type: ignore[assignment]
    if not has_str:
        cls.__str__ = build_str  # type: ignore[assignment]

    return cls


@typing.overload
def representation(cls: _ClassT, /, *fields: str, use_str: bool = False) -> _ClassT: ...


@typing.overload
def representation(
    *fields: str, use_str: bool = False
) -> typing.Callable[[_ClassT], _ClassT]: ...


def representation(
    *fields: typing.Any, use_str: bool = False
) -> typing.Union[_ClassT, typing.Callable[[_ClassT], _ClassT]]:
    return (
        _apply_representation(fields[0], fields[1:], use_str)
        if fields and inspect.isclass(fields[0])
        else lambda cls: _apply_representation(cls, fields, use_str)
    )
