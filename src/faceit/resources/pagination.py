from __future__ import annotations

import logging
import sys
import warnings
from inspect import Parameter, iscoroutinefunction, signature
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Final,
    Iterator,
    List,
    Literal,
    NamedTuple,
    Optional,
    Set,
    Union,
    cast,
    final,
    overload,
)

from annotated_types import Le
from pydantic.fields import FieldInfo

from faceit.constants import RAW_RESPONSE_ITEMS_KEY
from faceit.models import ItemPage, PaginationTimeRange
from faceit.types import Self, TypeAlias
from faceit.utils import check_required_attributes, deep_get, get_hashable_representation

from .base import BaseResource

_logger = logging.getLogger(__name__)


@final
class PaginationMaxParams(NamedTuple):
    limit: int
    offset: int


# Standard pagination parameter names `('limit', 'offset')` from PaginationMaxParams
# Used for validation and extraction in pagination methods
_PAGINATION_ARGS: Final = PaginationMaxParams._fields
_UNIX_PAGINATION_PARAMS: Final = PaginationTimeRange._fields  # `('start', 'to')` from PaginationTimeRange

_RawResponsePage: TypeAlias = Union[ItemPage, Dict[str, Any]]
_ExtractedItemsCollection: TypeAlias = Union[ItemPage, List[Dict[str, Any]]]

_SyncPaginationMethod: TypeAlias = Callable[..., _RawResponsePage]
_AsyncPaginationMethod: TypeAlias = Callable[..., Awaitable[_RawResponsePage]]
_PaginationMethod: TypeAlias = Union[_SyncPaginationMethod, _AsyncPaginationMethod]

_SyncPageFetcher: TypeAlias = Callable[[int], Optional[_ExtractedItemsCollection]]
_AsyncPageFetcher: TypeAlias = Callable[[int], Awaitable[Optional[_ExtractedItemsCollection]]]

# Type aliases to improve readability of pagination iterator signatures
_ItemsIterator = Iterator[_ExtractedItemsCollection]
_AsyncItemsIterator = AsyncIterator[_ExtractedItemsCollection]


if sys.version_info >= (3, 10):
    # Use built-in `anext()` when available, but create a private alias
    # to maintain consistent naming convention with our backport implementation
    _anext = anext
else:
    # Backport of the `anext()` built-in function introduced in Python 3.10
    # This allows using the same async iteration pattern regardless of Python version
    from faceit.types import TypeVar

    _T = TypeVar("_T")

    async def _anext(ait: AsyncIterator[_T]) -> _T:
        return await ait.__anext__()


def _concatenate_pages(
    accumulated_page: _ExtractedItemsCollection, new_page: _ExtractedItemsCollection, /
) -> Optional[_ExtractedItemsCollection]:
    # Pages can only be concatenated if they're of the same type (both `ItemPage` or both `list`)
    # `ItemPage` implements custom `__add__` method that handles pagination metadata
    # Split into separate `if` statements to satisfy mypy type checking and improve readability
    if isinstance(accumulated_page, ItemPage) and isinstance(new_page, ItemPage):
        return accumulated_page + new_page

    if isinstance(accumulated_page, list) and isinstance(new_page, list):
        return accumulated_page + new_page

    _logger.warning(
        "Cannot concatenate pages of different types: %s and %s",
        type(accumulated_page).__name__,
        type(new_page).__name__,
    )
    return None


def _extract_page_items(page: _RawResponsePage) -> Optional[_ExtractedItemsCollection]:
    """Extract items from a paginated response."""
    if isinstance(page, ItemPage):
        return page if page else None
    if not isinstance(page, dict):
        raise TypeError(f"Invalid page format: expected ItemPage or dict, got {type(page).__name__}")
    if RAW_RESPONSE_ITEMS_KEY not in page:
        raise TypeError(f"Missing required '{RAW_RESPONSE_ITEMS_KEY}' key in response")
    return page[RAW_RESPONSE_ITEMS_KEY] if page[RAW_RESPONSE_ITEMS_KEY] else None


def _extract_pagination_limits(
    limit_param: Parameter, offset_param: Parameter, method_name: str = "unknown"
) -> PaginationMaxParams:
    # These validations serve two purposes:
    # 1. For developers implementing methods - they ensure function signatures meet
    #    pagination requirements and fail early with clear error messages during development
    # 2. For static type checking - they allow mypy to verify we're working with correct types,
    #    catching potential type errors before runtime
    if limit_param.default is None or offset_param.default is None:
        raise ValueError(
            f"Function {method_name} is missing default value for {" or ".join(_PAGINATION_ARGS)} parameter"
        )
    if not isinstance(limit_param.default, FieldInfo) or not isinstance(offset_param.default, FieldInfo):
        raise ValueError(
            f"Default value for {" or ".join(_PAGINATION_ARGS)} parameter in {method_name} is not a FieldInfo"
        )

    limit_constraint = _get_le(limit_param)
    if limit_constraint is None:
        raise ValueError(f"In limit metadata of {method_name}, no Le constraint found")
    # We cast constraint values to `int` without additional type checking because:
    # 1. Le constraints in Pydantic's `Field()` only accept numeric types
    # 2. For pagination parameters, integers are the only sensible constraint type
    # 3. Type errors would be caught during development, not at runtime
    max_limit = cast(int, limit_constraint.le)
    offset_constraint = _get_le(offset_param)
    # `Offset` is optional, unlike the `limit`, so if it is not found,
    # consider that the maximum offset is equal to the maximum limit
    max_offset = max_limit if offset_constraint is None else cast(int, offset_constraint.le)
    return PaginationMaxParams(max_limit, max_offset)


def _extract_unix_timestamp(
    collection: _ExtractedItemsCollection, dict_unix_key: str, model_unix_attr: str
) -> Optional[int]:
    # NOTE: The API provides Unix timestamps in milliseconds, which may need to be
    # converted to seconds (divided by 1000) when creating datetime objects

    if not collection:
        return None

    last_item = collection[-1]
    if isinstance(last_item, dict):
        return deep_get(last_item, dict_unix_key)
    if hasattr(last_item, model_unix_attr):
        return getattr(last_item, model_unix_attr)

    warnings.warn(
        f"Could not extract Unix timestamp from item of type {type(last_item).__name__}.",
        UserWarning,
        stacklevel=2,
    )
    return None


def _get_le(param: Parameter, /) -> Optional[Le]:
    """Extract `Le` constraint from parameter metadata if present."""
    return next((items for items in param.default.metadata if isinstance(items, Le)), None)


def _has_unix_pagination_params(method: _PaginationMethod, /) -> bool:
    """Check if the `method` supports `Unix timestamp` pagination."""
    return all(param in signature(method).parameters for param in _UNIX_PAGINATION_PARAMS)


def _safe_create_iterator(
    method: _PaginationMethod,
    is_async_expected: bool,
    method_name_for_error: Literal["collect", "acollect"],
    *args: Any,
    **kwargs: Any,
) -> PaginatedIterator:
    iterator = PaginatedIterator(method, *args, **kwargs)
    if iterator._is_async != is_async_expected:
        sync_type, async_type = (
            ("synchronous", "asynchronous") if is_async_expected else ("asynchronous", "synchronous")
        )
        raise TypeError(
            f"Cannot use {async_type} collection with {sync_type} method {method.__name__}. "
            f"Use '{method_name_for_error}' instead."
        )
    return iterator


def _validate_unix_pagination_settings(
    method: _PaginationMethod,
    use_unix_pagination: bool,
    dict_unix_key: Optional[str],
    model_unix_attr: Optional[str],
    kwargs: Dict[str, Any],
) -> bool:
    if not use_unix_pagination:
        return False

    if not _has_unix_pagination_params(method):
        warnings.warn(
            f"Method {method.__name__} does not appear to support Unix timestamp pagination. "
            f"Expected {' and '.join(_UNIX_PAGINATION_PARAMS)} parameters.",
            UserWarning,
            stacklevel=3,
        )
        return False

    if any(not isinstance(value, str) or not value for value in (dict_unix_key, model_unix_attr)):
        raise ValueError(
            "When using Unix timestamp pagination, you must provide either 'dict_unix_key' or 'model_unix_attr' "
            "as a non-empty string. These parameters specify how to extract timestamps from items."
        )

    if any(kwargs.pop(arg, None) for arg in _UNIX_PAGINATION_PARAMS):
        warnings.warn(
            f"The parameters {', '.join(_UNIX_PAGINATION_PARAMS)} will be managed automatically "
            f"with Unix timestamp pagination. Your provided values will be ignored.",
            UserWarning,
            stacklevel=3,
        )

    return True


def check_pagination_support(func: Callable[..., Any], /) -> Union[PaginationMaxParams, Literal[False]]:
    """Check if a method supports pagination by examining its parameters.

    Verifies that the function:
    1. Is a method of a `BaseResource` subclass
    2. Has both `limit` and `offset` parameters
    3. Has proper constraints on these parameters

    Args:
        func: The function to check for pagination support

    Returns:
        `PaginationMaxParams` with pagination limits if supported, `False` otherwise
    """
    if not hasattr(func, "__self__") or not issubclass(func.__self__.__class__, BaseResource):
        return False

    limit_param, offset_param = (signature(func).parameters.get(arg) for arg in _PAGINATION_ARGS)

    if limit_param is None or offset_param is None:
        return False

    return _extract_pagination_limits(limit_param, offset_param, func.__name__)


def deduplicate_collection(collection: Optional[_ExtractedItemsCollection], /) -> Optional[_ExtractedItemsCollection]:
    """Remove duplicate items from a collection while preserving order.

    Uses hash-based deduplication to handle unhashable objects and maintains
    original pagination metadata for `ItemPage` collections.

    Args:
        collection: The collection to deduplicate (`ItemPage` or `list`)

    Returns:
        A new collection with duplicates removed, preserving the original order
        and metadata (for `ItemPage`). Returns None if input is None.
    """
    if collection is None:
        return None

    if not isinstance(collection, (ItemPage, list)):
        warnings.warn(
            f"Deduplication not supported for collection of type {type(collection).__name__}. "
            f"Expected 'ItemPage' or 'list'. The collection will be returned unchanged.",
            UserWarning,
            stacklevel=2,
        )
        return collection

    seen: Set[int] = set()
    unique_items = []
    for item in collection:
        item_hash = get_hashable_representation(item)
        if item_hash not in seen:
            unique_items.append(item)
            seen.add(item_hash)

    return (
        collection.model_copy(update={"items": unique_items, "limit": len(unique_items)})
        if isinstance(collection, ItemPage)
        else unique_items
    )


@final
class PaginatedIterator(_ItemsIterator, _AsyncItemsIterator):
    """Iterator for paginated API resources.

    Provides a unified interface for iterating through paginated resources,
    supporting both synchronous and asynchronous iteration depending on the
    underlying resource method.

    This class handles pagination details automatically, including:
    - Tracking pagination state (current offset, page index)
    - Detecting when all pages have been exhausted
    - Enforcing pagination limits
    - Supporting both sync and async iteration patterns
    """

    __slots__ = (
        "_exhausted",
        "_fetch_page",
        "_is_async",
        "_method",
        "_offset",
        "_page_index",
        "_pagination_limits",
    )

    def __init__(self, method: _PaginationMethod, /, *args: Any, **kwargs: Any) -> None:
        """Initialize a paginated iterator for the given method.

        Args:
            method: A resource method that supports pagination
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Raises:
            ValueError: If the method doesn't support pagination
        """
        pagination_limits = check_pagination_support(method)
        if pagination_limits is False:  # Checking for `False` seems preferable to me
            raise ValueError(
                f"Method '{method.__name__}' does not support pagination. "
                f"Ensure it's a BaseResource method with {" and ".join(_PAGINATION_ARGS)} parameters."
            )

        self._method = method
        self._pagination_limits = pagination_limits

        # Unwrap the method to find its original function object
        # This is necessary because some decorators (particularly `validate_uuid_args`)
        # don't preserve the coroutine status of async functions
        # By accessing the original unwrapped function, we can correctly
        # determine if the method is synchronous or asynchronous
        original_method = method
        while hasattr(original_method, "__wrapped__"):
            original_method = original_method.__wrapped__
        self._is_async = iscoroutinefunction(original_method)

        self._fetch_page = (self._build_async_page_fetcher if self._is_async else self._build_sync_page_fetcher)(
            *args, **self.__class__._remove_pagination_args(**kwargs)
        )

        self._init_iteration()

    def _init_iteration(self) -> None:
        self._exhausted = False
        self._page_index = 0
        self._offset = 0

    @property
    def pagination_limits(self) -> PaginationMaxParams:
        return self._pagination_limits

    @property
    def exhausted(self) -> bool:
        return self._exhausted

    @property
    def current_offset(self) -> int:
        return self._offset

    @current_offset.setter
    def current_offset(self, value: int) -> None:
        if self._exhausted:
            raise ValueError("Pagination offset cannot be set after the iterator has been exhausted")
        if value < 0:
            raise ValueError(f"Pagination offset cannot be negative: {value}")
        if value > self._pagination_limits.limit:
            raise ValueError(
                f"Pagination offset ({value}) cannot exceed the maximum limit ({self._pagination_limits.limit})"
            )
        self._offset = value

    @property
    def current_page_index(self) -> int:
        return self._page_index

    def reset(self) -> None:
        """Reset the iterator to its initial state.

        Resets the internal state of the iterator, allowing it to be reused
        from the beginning without creating a new instance.
        """
        self._init_iteration()

    def with_updated_args(self, *args: Any, **kwargs: Any) -> Self:
        """Create a new paginator with updated arguments but the same method.

        Returns a new instance of the paginator with the same method but different
        arguments, allowing for reuse of the paginator with modified parameters.

        Args:
            *args: New positional arguments to pass to the method
            **kwargs: New keyword arguments to pass to the method

        Returns:
            A new paginator instance with updated arguments
        """
        return self.__class__.with_method(self._method, *args, **kwargs)

    @classmethod
    def with_method(cls, method: _PaginationMethod, /, *args: Any, **kwargs: Any) -> Self:
        """Create a paginated iterator instance for the given method.

        This is an alternative constructor that creates an iterator bound to a specific
        paginated resource method.

        Args:
            method: A resource method that supports pagination
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Returns:
            A new paginated iterator instance
        """
        return cls(method, *args, **kwargs)

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}({self._method.__name__}, "
            f"{"exhausted" if self._exhausted else "active"}, offset={self._offset}, page_index={self._page_index})"
        )

    def __repr__(self) -> str:
        return (
            check_required_attributes(self, "_method", "_is_async", "_pagination_limits")
            or f"{self.__class__.__name__}("
            f"method={self._method.__name__!r}, "
            f"async={self._is_async}, "
            f"pagination_limits={self._pagination_limits}, "
            f"exhausted={self._exhausted}, "
            f"current_offset={self._offset}, "
            f"current_page_index={self._page_index})"
        )

    @staticmethod
    def _remove_pagination_args(**kwargs: Any) -> Dict[str, Any]:
        """Filter out pagination parameters from kwargs to prevent conflicts with internal pagination."""
        # More efficient to modify the existing dictionary in-place
        if any(kwargs.pop(arg, None) for arg in _PAGINATION_ARGS):
            warnings.warn(
                f"Pagination parameters {_PAGINATION_ARGS} should not be provided by users. "
                f"These parameters are managed internally by the pagination system. ",
                UserWarning,
                stacklevel=2,
            )
        return kwargs

    def _build_sync_page_fetcher(self, *args: Any, **kwargs: Any) -> _SyncPageFetcher:
        def fetch_page(offset: int) -> Optional[_ExtractedItemsCollection]:
            # fmt: off
            return _extract_page_items(cast(_SyncPaginationMethod, self._method)(
                *args, offset=offset, limit=self._pagination_limits.limit, **kwargs
            ))
            # fmt: on

        return fetch_page

    def _build_async_page_fetcher(self, *args: Any, **kwargs: Any) -> _AsyncPageFetcher:
        async def fetch_page(offset: int) -> Optional[_ExtractedItemsCollection]:
            # fmt: off
            return _extract_page_items(await cast(_AsyncPaginationMethod, self._method)(
                *args, offset=offset, limit=self._pagination_limits.limit, **kwargs
            ))
            # fmt: on

        return fetch_page

    def _handle_iteration_state(self, page: Optional[_ExtractedItemsCollection]) -> _ExtractedItemsCollection:
        if page is None:
            self._exhausted = True
            raise StopAsyncIteration if self._is_async else StopIteration

        self._page_index += 1
        self._offset += self._pagination_limits.limit
        self._exhausted = len(page) < self._pagination_limits.limit or self._offset >= self._pagination_limits.offset
        return page

    def __iter__(self) -> Self:
        if self._is_async:
            raise TypeError(
                f"Cannot use synchronous iteration with asynchronous method {self._method.__name__}. "
                f"Use 'async for' instead of 'for'."
            )
        return self

    def __next__(self) -> _ExtractedItemsCollection:
        if self._exhausted:
            raise StopIteration
        return self._handle_iteration_state(cast(_SyncPageFetcher, self._fetch_page)(self._offset))

    def __aiter__(self) -> Self:
        if not self._is_async:
            raise TypeError(
                f"Cannot use asynchronous iteration with synchronous method {self._method.__name__}. "
                f"Use 'for' instead of 'async for'."
            )
        return self

    async def __anext__(self) -> _ExtractedItemsCollection:
        if self._exhausted:
            raise StopAsyncIteration
        return self._handle_iteration_state(await cast(_AsyncPageFetcher, self._fetch_page)(self._offset))


@overload
def collect(
    method: _SyncPaginationMethod,
    /,
    *args: Any,
    deduplicate: bool = False,
    use_unix_pagination: Literal[False] = ...,
    dict_unix_key: None = ...,
    model_unix_attr: None = ...,
    **kwargs: Any,
) -> Optional[_ExtractedItemsCollection]: ...
@overload
def collect(
    method: _SyncPaginationMethod,
    /,
    *args: Any,
    deduplicate: bool = False,
    use_unix_pagination: Literal[True],
    dict_unix_key: str,
    model_unix_attr: str,
    **kwargs: Any,
) -> Optional[_ExtractedItemsCollection]: ...
def collect(
    method: _SyncPaginationMethod,
    /,
    *args: Any,
    deduplicate: bool = False,
    use_unix_pagination: bool = False,
    dict_unix_key: Optional[str] = None,
    model_unix_attr: Optional[str] = None,
    **kwargs: Any,
) -> Optional[_ExtractedItemsCollection]:
    """Collect all pages from a paginated method into a single collection.

    This function iterates through all pages of a paginated resource method
    and combines them into a single collection. It supports both standard pagination
    and Unix timestamp-based pagination for methods that accept `start` and `to` parameters.

    Args:
        method: A synchronous method that supports pagination
        *args: Positional arguments to pass to the method
        deduplicate: Whether to remove duplicate items from the result collection.
                     Use as a fallback when upstream API may return duplicates, though ideally data should be unique.
        use_unix_pagination: Whether to use Unix timestamp-based pagination
        dict_unix_key: The key to extract Unix timestamp from dictionary items (required if use_unix_pagination=True)
        model_unix_attr: The attribute name to extract Unix timestamp from model objects (required if use_unix_pagination=True)
        **kwargs: Keyword arguments to pass to the method

    Raises:
        ValueError: If Unix pagination is enabled but required parameters are missing
        TypeError: If the method is asynchronous (use `acollect` instead)

    Returns:
        A collection containing all items from all pages, or None if no items were found

    Note:
        For asynchronous methods, use `acollect` instead.
        For memory-efficient streaming of large datasets, use `PaginatedIterator` directly.
    """
    use_unix_pagination = _validate_unix_pagination_settings(
        method, use_unix_pagination, dict_unix_key, model_unix_attr, kwargs
    )

    iterator = _safe_create_iterator(method, False, "acollect", *args, **kwargs)

    try:
        collection = next(iterator)
    except StopIteration:
        return None

    for page in iterator:
        result = _concatenate_pages(collection, page)
        if result is not None:
            collection = result

    if not use_unix_pagination:
        return collection

    # We use `cast(str, ...)` as mypy cannot correctly infer that these values
    # have been validated in `_validate_unix_pagination_settings()`
    # This ensures proper type checking while maintaining runtime safety
    def get_last_item_timestamp(collection: _ExtractedItemsCollection) -> Optional[int]:
        return _extract_unix_timestamp(collection, cast(str, dict_unix_key), cast(str, model_unix_attr))

    # Store previous timestamp to prevent infinite loops when pagination reaches the end
    timestamp, prev_timestamp = get_last_item_timestamp(collection), None
    while timestamp is not None and timestamp != prev_timestamp:
        iterator = iterator.with_updated_args(*args, **{**kwargs, _UNIX_PAGINATION_PARAMS[1]: timestamp + 1})

        for page in iterator:
            result = _concatenate_pages(collection, page)
            if result is not None:
                collection = result

        timestamp, prev_timestamp = get_last_item_timestamp(collection), timestamp

    return deduplicate_collection(collection) if deduplicate else collection


@overload
async def acollect(
    method: _AsyncPaginationMethod,
    /,
    *args: Any,
    deduplicate: bool = False,
    use_unix_pagination: Literal[False] = ...,
    dict_unix_key: None = ...,
    model_unix_attr: None = ...,
    **kwargs: Any,
) -> Optional[_ExtractedItemsCollection]: ...
@overload
async def acollect(
    method: _AsyncPaginationMethod,
    /,
    *args: Any,
    deduplicate: bool = False,
    use_unix_pagination: Literal[True],
    dict_unix_key: str,
    model_unix_attr: str,
    **kwargs: Any,
) -> Optional[_ExtractedItemsCollection]: ...
async def acollect(
    method: _AsyncPaginationMethod,
    /,
    *args: Any,
    deduplicate: bool = False,
    use_unix_pagination: bool = False,
    dict_unix_key: Optional[str] = None,
    model_unix_attr: Optional[str] = None,
    **kwargs: Any,
) -> Optional[_ExtractedItemsCollection]:
    """Asynchronously collect all pages from a paginated method into a single collection.

    This function iterates through all pages of a paginated resource method
    and combines them into a single collection. It supports both standard pagination
    and Unix timestamp-based pagination for methods that accept `start` and `to` parameters.

    Args:
        method: An asynchronous method that supports pagination
        *args: Positional arguments to pass to the method
        deduplicate: Whether to remove duplicate items from the result collection.
                     Use as a fallback when upstream API may return duplicates, though ideally data should be unique.
        use_unix_pagination: Whether to use Unix timestamp-based pagination
        dict_unix_key: The key to extract Unix timestamp from dictionary items (required if use_unix_pagination=True)
        model_unix_attr: The attribute name to extract Unix timestamp from model objects (required if use_unix_pagination=True)
        **kwargs: Keyword arguments to pass to the method

    Raises:
        ValueError: If Unix pagination is enabled but required parameters are missing
        TypeError: If the method is synchronous (use `collect` instead)

    Returns:
        A collection containing all items from all pages, or None if no items were found

    Note:
        For synchronous methods, use `collect` instead.
        For memory-efficient streaming of large datasets, use `PaginatedIterator` directly.
    """
    use_unix_pagination = _validate_unix_pagination_settings(
        method, use_unix_pagination, dict_unix_key, model_unix_attr, kwargs
    )

    iterator = _safe_create_iterator(method, True, "collect", *args, **kwargs)

    try:
        collection = await _anext(iterator)
    except StopAsyncIteration:
        return None

    async for page in iterator:
        result = _concatenate_pages(collection, page)
        if result is not None:
            collection = result

    if not use_unix_pagination:
        return collection

    def get_last_item_timestamp(collection: _ExtractedItemsCollection) -> Optional[int]:
        return _extract_unix_timestamp(collection, cast(str, dict_unix_key), cast(str, model_unix_attr))

    timestamp, prev_timestamp = get_last_item_timestamp(collection), None
    while timestamp is not None and timestamp != prev_timestamp:
        iterator = iterator.with_updated_args(*args, **{**kwargs, _UNIX_PAGINATION_PARAMS[1]: timestamp + 1})

        async for page in iterator:
            result = _concatenate_pages(collection, page)
            if result is not None:
                collection = result

        timestamp, prev_timestamp = get_last_item_timestamp(collection), timestamp

    return deduplicate_collection(collection) if deduplicate else collection
