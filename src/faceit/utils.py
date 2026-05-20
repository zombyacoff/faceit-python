from __future__ import annotations

import inspect
import json
import reprlib
import sys
from contextlib import suppress
from enum import Enum, auto
from functools import lru_cache, reduce, wraps
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, TypeVar, cast, overload
from uuid import UUID

from typing_extensions import Self, TypeIs

if TYPE_CHECKING:
    from asyncio import Lock as AsyncLock  # noqa: ICN003
    from collections.abc import Awaitable, Callable, Iterable, Mapping
    from threading import Lock as SyncLock
    from types import FrameType

    from .types import _P, _T, ValidUUID

    _CallableT = TypeVar("_CallableT", bound=Callable[..., Any])
    _ClassT = TypeVar("_ClassT", bound=type)


# NOTE: Inspired by irgeek/StrEnum:
# https://github.com/irgeek/StrEnum/blob/master/strenum/__init__.py#L21
# Previously depended on `StrEnum`, but only core features were needed -
# now implemented inline to avoid extra dependencies.
class StrEnum(str, Enum):
    _value_: str

    def __new__(cls, value: str | auto, *args: object, **kwargs: object) -> Self:
        if isinstance(value, str | auto):
            return super().__new__(cls, value, *args, **kwargs)
        msg = f"StrEnum values must be of type 'str', but got {type(value).__name__}: {value!r}"  # type: ignore[unreachable]
        raise TypeError(msg)

    @staticmethod
    def _generate_next_value_(name: str, *_: object, **__: object) -> str:
        return name

    def __str__(self) -> str:
        return str(self.value)


class StrEnumWithAll(StrEnum):
    @classmethod
    def get_all_values(cls) -> tuple[Self, ...]:
        return tuple(cls)


def locked(
    lock: SyncLock | AsyncLock, /
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    def decorator(func: Callable[_P, _T], /) -> Callable[_P, _T]:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
                async with cast("AsyncLock", lock):  # Developer's responsibility
                    return cast("_T", await func(*args, **kwargs))

            return cast("Callable[_P, _T]", async_wrapper)

        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            with cast("SyncLock", lock):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def extends(_: _CallableT, /) -> Callable[[Callable[..., object]], _CallableT]:
    """
    Decorator that assigns the type signature of the given function to the
    decorated function. Type checking is enforced only at the function boundary
    (when calling the function), not within the function body.
    """
    return lambda x: cast("_CallableT", x)


async def invoke_callable(
    func: Callable[..., _T | Awaitable[_T]],
    /,
    *args: Any,
    **kwargs: Any,
) -> _T:
    if not callable(func):
        msg = (  # type: ignore[unreachable]
            f"Expected a callable object, got {type(func).__name__} ({func!r}). "
            "Argument 'func' must be a function or object with a __call__ method."
        )
        raise TypeError(msg)
    result = func(*args, **kwargs)
    if inspect.isawaitable(result):
        result = await result
    return cast("_T", result)


def deep_get(
    dictionary: Mapping[str, Any],
    keys: str,
    /,
    default: _T | None = None,
) -> _T | Any | None:
    current = dictionary
    try:
        for key in keys.split("."):
            current = current[key]
    except (KeyError, TypeError, AttributeError):
        return default
    return current


def get_nested_property(
    obj: Any, path: str, /, default: _T | None = None
) -> _T | Any | None:
    if obj is None or not path:
        return default
    try:
        return reduce(
            lambda o, k: default if o is None else getattr(o, k), path.split("."), obj
        )
    except (AttributeError, TypeError):
        return default


def get_hashable_representation(obj: Any, /) -> int:
    with suppress(TypeError):
        return hash(obj)
    try:
        obj_str = json.dumps(obj, default=str, sort_keys=True)
    except (TypeError, AttributeError):
        obj_str = str(obj)
    return int.from_bytes(sha256(obj_str.encode()).digest()[:8], "big", signed=True)


def deduplicate_unhashable(values: Iterable[_T], /) -> list[_T]:
    return list({get_hashable_representation(v): v for v in values}.values())


_UUID_BYTES: Final = 16


def to_uuid(value: str | bytes, /) -> UUID:
    if isinstance(value, str):
        return UUID(value)
    if not isinstance(value, bytes):
        msg = f"Expected str or bytes for UUID conversion, got {type(value).__name__}"  # type: ignore[unreachable]
        raise TypeError(msg)
    try:
        return UUID(value.decode())
    except UnicodeDecodeError as e:
        if len(value) == _UUID_BYTES:
            return UUID(bytes=value)
        msg = "Byte value must be a UTF-8 encoded UUID string or 16 bytes"
        raise ValueError(msg) from e


def is_valid_uuid(value: Any, /) -> TypeIs[ValidUUID]:
    if isinstance(value, UUID):
        return True
    if not isinstance(value, str | bytes):
        return False
    try:
        to_uuid(value)
    except (AttributeError, ValueError):
        return False
    return True


def create_uuid_validator(
    *,
    arg_name: str = "value",
    error_message: str | None = None,
) -> Callable[[Any], str]:
    if error_message is None:
        error_message = "Invalid {arg_name}: {value}. Expected a valid UUID."

    def validator(value: Any, /) -> str:
        if is_valid_uuid(value):
            return str(value if isinstance(value, UUID | str) else to_uuid(value))
        raise ValueError(error_message.format(arg_name=arg_name, value=value))

    return validator


def validate_positive_int(value: Any, /, param_name: str = "value") -> int:
    """
    Utility for validating that a value is a positive integer.
    Use this when :class:`pydantic.PositiveInt` type or validation is
    impractical or unavailable.
    """
    if not isinstance(value, int):
        msg = f"{param_name!r} must be int, got {type(value).__name__}"
        raise TypeError(msg)
    if value <= 0:
        msg = f"{param_name!r} must be a positive integer, got {value}"
        raise ValueError(msg)
    return value


_IGNORED_MODULES: Final = {
    "pydantic",
}


@lru_cache(maxsize=1)
def _get_ignored_paths() -> tuple[
    tuple[Path, ...],
    frozenset[Path],
]:
    prefixes: list[Path] = []
    files: set[Path] = set()

    for mod_name in (__name__.split(".")[0], *_IGNORED_MODULES):
        mod = sys.modules.get(mod_name)
        if mod is None or not hasattr(mod, "__file__") or mod.__file__ is None:
            continue

        path = Path(mod.__file__).resolve()
        if path.name == "__init__.py":
            prefixes.append(path.parent)
        else:
            files.add(path)

    return tuple(prefixes), frozenset(files)


def find_user_stacklevel() -> int:
    """
    Determines the appropriate stack level for warnings emitted by the library,
    so that they point to the user's code instead of internal library frames.
    """
    with suppress(ValueError, AttributeError):
        ignored_prefixes, ignored_files = _get_ignored_paths()
        frame: FrameType | None = sys._getframe(1)
        level = 1

        while frame:
            filename = frame.f_code.co_filename
            if filename and not filename.startswith("<"):
                path = Path(filename).resolve()
                is_user_code = path not in ignored_files and not any(
                    prefix in path.parents or path == prefix
                    for prefix in ignored_prefixes
                )
                if is_user_code:
                    return level

            frame = frame.f_back
            level += 1

    return 1


_UNINITIALIZED_MARKER: Final = "uninitialized"


def _format_fields(obj: object, fields: tuple[str, ...], *, joiner: str) -> str:
    return (
        joiner.join(f"{field}={reprlib.repr(getattr(obj, field))}" for field in fields)
        if all(hasattr(obj, field) for field in fields)
        else repr(_UNINITIALIZED_MARKER)
    )


def _apply_representation(
    cls: _ClassT,
    fields: tuple[str, ...],
    use_str: bool,  # noqa: FBT001
) -> _ClassT:
    has_str = getattr(cls, "__str__", object.__str__) is not object.__str__

    if use_str and not has_str:
        msg = f"Class {cls.__name__} must define '__str__' method when 'use_str=True'"
        raise TypeError(msg)

    def build_repr(self: _ClassT) -> str:
        str_args = f"'{self}'" if use_str else _format_fields(self, fields, joiner=", ")
        return f"{self.__class__.__name__}({str_args})"

    def build_str(self: _ClassT) -> str:
        return _format_fields(self, fields, joiner=" ")

    cls.__repr__ = build_repr  # type: ignore[assignment]
    if not has_str:
        cls.__str__ = build_str  # type: ignore[assignment]

    return cls


@overload
def representation(
    cls: _ClassT,
    /,
    *fields: str,
    use_str: bool = ...,
) -> _ClassT: ...
@overload
def representation(
    *fields: str,
    use_str: bool = ...,
) -> Callable[[_ClassT], _ClassT]: ...
def representation(
    *fields: Any,
    use_str: bool = False,
) -> _ClassT | Callable[[_ClassT], _ClassT]:
    return (
        _apply_representation(fields[0], fields[1:], use_str)
        if fields and inspect.isclass(fields[0])
        else lambda cls: _apply_representation(cls, fields, use_str)
    )
