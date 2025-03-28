import pickle
from datetime import datetime
from functools import reduce, wraps
from inspect import signature
from typing import Any, Callable, Literal, Mapping, Optional, TypeVar, Union
from uuid import UUID

from .types import ParamSpec

_T = TypeVar("_T")
_P = ParamSpec("_P")

# NOTE: While similar utility functions likely exist in third-party libraries,
# we've chosen to implement them directly to minimize external dependencies
# This approach reduces project complexity and potential version conflicts
# while maintaining full control over the implementation details


def deep_get(dictionary: Mapping[str, Any], keys: str, default: Optional[_T] = None) -> Union[Any, _T]:
    """Retrieve a nested value from a dictionary using dot notation.

    Args:
        dictionary: The source dictionary to retrieve values from
        keys: Key path in dot notation (e.g., "user.profile.name")
        default: Default value to return if the path doesn't exist

    Returns:
        The value at the specified path or the default value if not found
    """
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, Mapping) else default, keys.split("."), dictionary
    )


def get_nested_property(obj: Any, path: str, default: Optional[_T] = None) -> Union[Any, _T]:
    """Retrieve a nested attribute from an object using dot notation.

    Args:
        obj: The source object to retrieve attributes from
        path: Attribute path in dot notation (e.g., "player.nickname")
        default: Default value to return if the attribute doesn't exist or if any
                 object in the path is None (defaults to None)

    Returns:
        The value of the nested attribute or the default value if not found
    """
    if obj is None or not path:
        return default
    try:
        return reduce(lambda o, k: getattr(o, k) if o is not None else default, path.split("."), obj)
    except (AttributeError, TypeError):
        return default


def get_hashable_representation(obj: Any) -> int:
    """Get a hashable integer representation of any object.

    For hashable objects, returns their hash directly.
    For unhashable objects, serializes them with pickle and hashes the result.
    """
    try:
        return hash(obj)
    except TypeError:
        return hash(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL))


# The API provides Unix timestamps in milliseconds
def convert_to_unix_millis(value: Optional[datetime]) -> Optional[int]:
    """Safe conversion of `datetime` to Unix timestamp in milliseconds."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return int(value.timestamp()) * 1000
    raise ValueError(f"Expected 'datetime' or 'None', got {type(value).__name__}")


# We maintain our own `UUID` validation implementation despite potentially more efficient alternatives.
# This specific implementation is crucial for the library's internal logic to distinguish between
# different resource types (e.g., nickname vs ID) and supports the expected behavior of various resource handlers
def is_valid_uuid(value: Any) -> bool:
    """Check if the given value is a valid UUID."""
    if isinstance(value, UUID):
        return True
    if not isinstance(value, (str, bytes)):
        return False
    try:
        UUID(value if isinstance(value, str) else value.decode())
        return True
    except (ValueError, AttributeError):
        return False


def validate_uuid_args(
    *arg_names: str, error_message: Optional[str] = None
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    """Decorator that validates specified arguments are valid UUIDs.

    Args:
        *arg_names: Names of arguments to validate
        error_message: Custom error message (optional)

    Raises:
        ValueError: If any specified argument is not a valid UUID

    Returns:
        Decorated function that validates UUID arguments
    """

    def decorator(func: Callable[_P, _T]) -> Callable[_P, _T]:
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
                    raise ValueError(error_message or f"Invalid {arg_name}: {value}. Must be a valid UUID.")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def check_required_attributes(obj: Any, *attrs: str) -> Union[Literal[False], str]:
    """Check if an object is missing any of the specified attributes.

    Args:
        obj: The object to check
        *attrs: Variable number of attribute names to verify

    Returns:
        False if all attributes are present, or a string with
        class name and 'uninitialized' if any attribute is missing
    """
    return False if all(hasattr(obj, attr) for attr in attrs) else f"{obj.__class__.__name__}('uninitialized')"
