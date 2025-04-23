from __future__ import annotations

import math
import typing as t
from abc import ABC
from inspect import Parameter, signature
from itertools import chain
from warnings import warn

from annotated_types import Le
from pydantic import PositiveInt
from pydantic.fields import FieldInfo
from strenum import StrEnum

from faceit._typing import (
    AsyncPaginationMethod,
    AsyncUnixPaginationMethod,
    BaseUnixPaginationMethod,
    PaginationMethodT,
    RawAPIItem,
    RawAPIPageResponse,
    Self,
    SyncPaginationMethod,
    SyncUnixPaginationMethod,
    TypeAlias,
)
from faceit._utils import (
    UnsetValue,
    deduplicate_unhashable,
    deep_get,
    lazy_import,
    representation,
    validate_positive_int,
)
from faceit.constants import RAW_RESPONSE_ITEMS_KEY
from faceit.models import ItemPage
from faceit.models._item_page import PaginationTimeRange

if t.TYPE_CHECKING:
    from .base import BaseResource

    _OptionalTimestampPaginationConfig: TypeAlias = t.Union[
        "TimestampPaginationConfig", t.Literal[False]
    ]


@lazy_import
def _get_base_resource_class() -> t.Type[BaseResource]:
    from .base import BaseResource  # noqa: PLC0415

    return BaseResource


_T = t.TypeVar("_T")

_PageType: TypeAlias = t.Union[ItemPage, RawAPIPageResponse]
_PageListType: TypeAlias = t.List[_PageType]
_PageT = t.TypeVar("_PageT", bound=_PageType)

# We use `PositiveInt` for Pydantic validation where available (e.g., with
# `@validate_call` in resource methods). However, in this module we implement
# our own validation logic for greater flexibility, as Pydantic-based validation
# is not always practical here.
MaxItemsType: TypeAlias = t.Union["MaxItems", PositiveInt]


@t.final
class TimestampPaginationConfig(t.TypedDict):
    key: str
    attr: str


@t.final
class PaginationMaxParams(t.NamedTuple):
    limit: int
    offset: int


@t.final
class MaxPages(int):
    """
    Indicates the maximum number of pages to fetch when passed as `max_items`.

    This class enables explicit page-based limits without introducing a separate
    `max_pages` parameter, allowing for flexible and concise API usage.

    **Developer rationale:**
    This dedicated class enables explicit page-based limits via the `max_items`
    parameter, without introducing a separate `max_pages` argument. Using a
    distinct type allows for clear and robust isinstance checks, making the
    API flexible and concise while keeping downstream logic simple and safe.
    """

    __slots__ = ()


class CollectReturnFormat(StrEnum):
    FIRST = "first"
    RAW = "raw"
    MODEL = "model"


class MaxItems(StrEnum):
    SAFE = "safe"


_UNIX_METHOD_REQUIRED_KEYS: t.Final[t.FrozenSet[str]] = frozenset(
    TimestampPaginationConfig.__annotations__.keys()
)
_PAGINATION_ARGS = PaginationMaxParams._fields
_UNIX_PAGINATION_PARAMS = PaginationTimeRange._fields


def _has_unix_pagination_params(method: BaseUnixPaginationMethod, /) -> bool:
    return all(
        param in signature(method).parameters
        for param in _UNIX_PAGINATION_PARAMS
    )


def _get_le(param: Parameter, /) -> t.Optional[Le]:
    return next(
        (items for items in param.default.metadata if isinstance(items, Le)),
        None,
    )


def _extract_pagination_limits(
    limit_param: Parameter, offset_param: Parameter, /, *, method_name: str
) -> PaginationMaxParams:
    # Validates pagination parameters for:
    # 1. Development - ensures correct function signatures with clear error messages
    # 2. Static typing - enables mypy to verify type correctness
    if limit_param.default is None or offset_param.default is None:
        raise ValueError(
            f"Function {method_name} missing "
            f"default value for limit/offset parameter"
        )
    if not isinstance(limit_param.default, FieldInfo) or not isinstance(
        offset_param.default, FieldInfo
    ):
        raise TypeError(
            f"Default for limit/offset in {method_name} is not a FieldInfo"
        )

    limit_constraint = _get_le(limit_param)
    if limit_constraint is None:
        raise ValueError(
            f"In limit metadata of {method_name}, no Le constraint found"
        )
    # Cast to `int` is safe because:
    # - Le constraints only accept numeric types
    # - Pagination parameters use integers
    max_limit = t.cast(int, limit_constraint.le)
    offset_constraint = _get_le(offset_param)
    max_offset = (
        UnsetValue.UNSET
        if offset_constraint is None
        else t.cast(int, offset_constraint.le)
    )
    return PaginationMaxParams(max_limit, max_offset)


def check_pagination_support(
    func: t.Callable[..., t.Any], /
) -> t.Union[PaginationMaxParams, t.Literal[False]]:
    if not hasattr(func, "__self__") or not issubclass(
        func.__self__.__class__, _get_base_resource_class()
    ):
        return False

    limit_param, offset_param = (
        signature(func).parameters.get(arg) for arg in _PAGINATION_ARGS
    )

    if limit_param is None or offset_param is None:
        return False

    return _extract_pagination_limits(
        limit_param, offset_param, method_name=func.__name__
    )


class _MethodCall(t.NamedTuple, t.Generic[PaginationMethodT]):
    call: PaginationMethodT
    args: t.Tuple[t.Any, ...]
    kwargs: t.Dict[str, t.Any]


class _MaxItemsInfo(t.NamedTuple):
    max_items: MaxItemsType
    last_page_remainder: int
    is_partial_last_page: bool

    @classmethod
    def from_max_pages(cls, max_pages: MaxItemsType, /) -> Self:
        return cls(max_pages, 0, False)


_ITERATOR_SLOTS = (
    "_exhausted",
    "_max_items_info",
    "_max_pages",
    "_method",
    "_offset",
    "_page_index",
    "_pagination_limits",
)


@representation(*_ITERATOR_SLOTS)
class BasePageIterator(t.Generic[PaginationMethodT, _PageT], ABC):
    __slots__ = _ITERATOR_SLOTS

    _STOP_ITERATION_EXC: t.ClassVar[t.Type[Exception]]

    _COLLECT_RETURN_FORMATS: t.ClassVar[
        t.Dict[
            CollectReturnFormat,
            t.Callable[
                [_PageListType],
                t.Union[t.Type[ItemPage], t.Type[RawAPIPageResponse]],
            ],
        ]
    ] = {
        CollectReturnFormat.FIRST: lambda collection: type(collection[0])
        if collection
        else RawAPIPageResponse,
        CollectReturnFormat.RAW: lambda _: RawAPIPageResponse,
        CollectReturnFormat.MODEL: lambda _: ItemPage,
    }

    SAFE_MAX_PAGES: t.ClassVar = 100

    DEFAULT_MAX_ITEMS: t.ClassVar = 2000
    """
    Selected as an optimal default to balance performance and resource usage
    when iterating through paginated FACEIT API data. 2000 is a multiple of
    both 100 and 20, the most common per-request limits in the FACEIT API,
    ensuring efficient pagination and minimal overhead.
    """

    timestamp_cfg: t.ClassVar = TimestampPaginationConfig

    def __init__(
        self,
        method: PaginationMethodT,
        /,
        *args: t.Any,
        max_items: MaxItemsType = DEFAULT_MAX_ITEMS,
        **kwargs: t.Any,
    ) -> None:
        pagination_limits = check_pagination_support(method)
        if pagination_limits is False:
            raise ValueError(
                f"Method '{method.__name__}' does not support pagination. "
                f"Ensure it's a BaseResource method "
                f"with offset and limit parameters."
            )
        if t.TYPE_CHECKING:
            # Use a function here because mypy does not allow direct assignment of
            # `_MethodCall[PaginationMethodT]` due to "Can't use bound type variable"
            # errors. This preserves type checking without runtime issues.
            def method_call(
                *_: t.Any, **__: t.Any
            ) -> _MethodCall[PaginationMethodT]: ...
        else:
            method_call = _MethodCall
        self._method = method_call(
            call=method,
            args=args,
            kwargs=self.__class__._remove_pagination_args(**kwargs),
        )
        self._pagination_limits = pagination_limits
        self._max_pages_setter(max_items)
        self._init_iteration()

    def _init_iteration(self) -> None:
        self._exhausted = False
        self._offset = 0
        self._page_index = 0

    @property
    def max_items(self) -> int:
        return self._max_pages * self._pagination_limits.limit

    @max_items.setter
    def max_items(self, value: int, /) -> None:
        self._max_pages_setter(value)

    @property
    def exhausted(self) -> bool:
        return self._exhausted

    @property
    def current_offset(self) -> int:
        return self._offset

    @current_offset.setter
    def current_offset(self, value: int, /) -> None:
        validate_positive_int(value, param_name="offset")
        if self._exhausted:
            raise ValueError(
                "Pagination offset cannot be set "
                "after the iterator has been exhausted"
            )
        if value > self._pagination_limits.limit:
            raise ValueError(
                f"Pagination offset cannot exceed the maximum limit "
                f"({self._pagination_limits.limit}): {value}"
            )
        self._offset = value

    @property
    def current_page_index(self) -> int:
        return self._page_index

    @property
    def _effective_limit(self) -> int:
        return (
            self._max_items_info.last_page_remainder
            if self._max_items_info.is_partial_last_page
            and self._page_index == self._max_pages - 1
            else self._pagination_limits.limit
        )

    def reset(self) -> None:
        self._init_iteration()

    def with_updated_args(self, *args: t.Any, **kwargs: t.Any) -> Self:
        return self.__class__(self._method.call, *args, **kwargs)

    def _max_pages_setter(self, max_items: t.Union[MaxItems, int], /) -> None:
        def set_max_pages(max_pages: int, /) -> None:
            self._max_pages = max_pages
            self._max_items_info = _MaxItemsInfo.from_max_pages(max_pages)

        def warn_if_exceeds_safe(max_pages: int, /) -> int:
            if max_pages > self.__class__.SAFE_MAX_PAGES:
                warn(
                    f"The computed number of pages ({max_pages}) exceeds the "
                    f"recommended safe maximum ({self.__class__.SAFE_MAX_PAGES}). "
                    f"Proceed at your own risk.",
                    UserWarning,
                    stacklevel=2,
                )
            return max_pages

        if max_items == MaxItems.SAFE:
            set_max_pages(self.__class__.SAFE_MAX_PAGES)
            return

        validate_positive_int(max_items, param_name="max_items")

        if isinstance(max_items, MaxPages):
            set_max_pages(warn_if_exceeds_safe(max_items))
            return

        last_page_remainder = max_items % self._pagination_limits.limit
        self._max_items_info = _MaxItemsInfo(
            max_items, last_page_remainder, last_page_remainder != 0
        )
        self._max_pages = warn_if_exceeds_safe(
            math.ceil(max_items / self._pagination_limits.limit)
        )

    def _handle_iteration_state(self, page: t.Optional[_PageT], /) -> _PageT:
        if page is None:
            self._exhausted = True
            raise self.__class__._STOP_ITERATION_EXC

        self._page_index += 1

        is_page_smaller_than_limit = (
            len(
                page[RAW_RESPONSE_ITEMS_KEY]
                if isinstance(page, dict)
                else page
            )
            < self._pagination_limits.limit
        )
        is_offset_exceeded = (
            False
            if self._pagination_limits.offset == UnsetValue.UNSET
            else self._offset >= self._pagination_limits.offset
        )
        is_max_items_reached = self._page_index >= self._max_pages
        self._exhausted = (
            is_page_smaller_than_limit
            or is_offset_exceeded
            or is_max_items_reached
        )

        self._offset += self._pagination_limits.limit
        return page

    @staticmethod
    def _remove_pagination_args(**kwargs: t.Any) -> t.Dict[str, t.Any]:
        if any(kwargs.pop(arg, None) for arg in _PAGINATION_ARGS):
            warn(
                f"Pagination parameters {_PAGINATION_ARGS} should not be "
                f"provided by users. These parameters are managed internally "
                f"by the pagination system.",
                UserWarning,
                stacklevel=2,
            )
        return kwargs

    @staticmethod
    def _validate_unix_pagination_parameter(
        method: PaginationMethodT,
        /,
        # Process `kwargs` to filter pagination parameters and issue warnings
        # when user-provided values will be ignored
        kwargs: t.Dict[str, t.Any],
        key: str,
        attr: str,
    ) -> None:
        if not _has_unix_pagination_params(method):
            raise ValueError(
                f"Method {method.__name__} does not appear "
                f"to support Unix timestamp pagination. "
                f"Expected start and to parameters."
            )
        if any(
            not isinstance(value, str) or not value for value in (key, attr)
        ):
            raise ValueError(
                f"Key and attribute parameters must be non-empty strings: {key}, {attr}"
            )
        if any(kwargs.pop(arg, None) for arg in _UNIX_PAGINATION_PARAMS):
            warn(
                "The parameters start and to will be managed automatically "
                "with Unix timestamp pagination. Your provided values will "
                "be ignored.",
                UserWarning,
                stacklevel=3,
            )

    @staticmethod
    def _validate_unix_config(
        unix_config: _OptionalTimestampPaginationConfig, /
    ) -> None:
        if unix_config is not False and not isinstance(unix_config, dict):
            raise ValueError(
                f"Invalid unix pagination configuration: expected "
                f"UnixPaginationConfig dictionary or False, got "
                f"{type(unix_config)}. See pagination.UnixPaginationConfig "
                "for the required format."
            )
        if (
            isinstance(unix_config, dict)
            and _UNIX_METHOD_REQUIRED_KEYS - unix_config.keys()
        ):
            raise ValueError(
                f"Invalid unix pagination configuration: "
                f"missing required keys {tuple(_UNIX_METHOD_REQUIRED_KEYS)}. "
                f"See pagination.UnixPaginationConfig for the required format."
            )

    @staticmethod
    def _extract_unix_timestamp(
        page: t.Optional[_PageT], key: str, attr: str, /
    ) -> t.Optional[int]:
        if not page:
            return None
        return (
            deep_get(page[RAW_RESPONSE_ITEMS_KEY][-1], key)
            if isinstance(page, dict)
            else getattr(page.last(), attr, None)
        )

    @staticmethod
    def _filter_collection(
        collection: t.List[_PageT], expected_type: t.Type[t.Any], /
    ) -> t.List[t.Any]:
        return [item for item in collection if isinstance(item, expected_type)]

    @staticmethod
    def _extract_items_from_raw_pages(
        pages: t.List[RawAPIPageResponse], /
    ) -> t.List[RawAPIItem]:
        return list(
            chain.from_iterable(page[RAW_RESPONSE_ITEMS_KEY] for page in pages)
        )

    @classmethod
    def _process_collected_pages(
        cls,
        collection: t.List[_PageT],
        return_format: CollectReturnFormat,
        deduplicate: bool,
        /,
    ) -> t.Union[ItemPage[_T], t.List[RawAPIItem]]:
        is_raw_mode = (
            cls._COLLECT_RETURN_FORMATS[return_format](
                t.cast(_PageListType, collection)
            )
            is dict
        )
        filtered = cls._filter_collection(
            collection, dict if is_raw_mode else ItemPage
        )
        processed = (
            cls._extract_items_from_raw_pages(filtered)
            if is_raw_mode
            else ItemPage.merge(filtered)
        )
        return (
            cls._deduplicate_collection(processed)
            if deduplicate
            else processed
        )

    @classmethod
    def _deduplicate_collection(
        cls, collection: t.Union[ItemPage, t.List[RawAPIItem]], /
    ) -> t.Union[ItemPage, t.List[RawAPIItem]]:
        unique_items = deduplicate_unhashable(collection)
        return (
            collection.with_items(unique_items)
            if isinstance(collection, ItemPage)
            else unique_items
        )

    @classmethod
    def _create_unix_timestamp_iterator(
        cls,
        method: PaginationMethodT,
        /,
        *args: t.Any,
        timestamp: t.Optional[int],
        **kwargs: t.Any,
    ) -> Self:
        # fmt: off
        return cls(method, *args, **{
            **kwargs,
            **({} if timestamp is None else {"to": timestamp + 1}),
        })
        # fmt: on


del _ITERATOR_SLOTS


class _BaseSyncPageIterator(
    BasePageIterator[
        t.Union[
            SyncPaginationMethod[_PageT], SyncUnixPaginationMethod[_PageT]
        ],
        _PageT,
    ],
    t.Iterator[_PageT],
):
    __slots__ = ()

    _STOP_ITERATION_EXC: t.ClassVar = StopIteration

    def _fetch_page(self) -> t.Optional[_PageT]:
        return (
            self._method.call(
                *self._method.args,
                **self._method.kwargs,
                limit=self._effective_limit,
                offset=self._offset,
            )
            or None
        )

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> _PageT:
        if self._exhausted:
            raise self.__class__._STOP_ITERATION_EXC
        return self._handle_iteration_state(self._fetch_page())


class _BasyAsyncPageIterator(
    BasePageIterator[
        t.Union[
            AsyncPaginationMethod[_PageT], AsyncUnixPaginationMethod[_PageT]
        ],
        _PageT,
    ],
    t.AsyncIterator[_PageT],
):
    __slots__ = ()

    _STOP_ITERATION_EXC: t.ClassVar = StopAsyncIteration

    async def _fetch_page(self) -> t.Optional[_PageT]:
        return (
            await self._method.call(
                *self._method.args,
                **self._method.kwargs,
                limit=self._effective_limit,
                offset=self._offset,
            )
            or None
        )

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> _PageT:
        if self._exhausted:
            raise self.__class__._STOP_ITERATION_EXC
        return self._handle_iteration_state(await self._fetch_page())


@t.final
class SyncPageIterator(_BaseSyncPageIterator[_PageT]):
    __slots__ = ()

    @t.overload
    def collect(
        self: SyncPageIterator[ItemPage[_T]],
    ) -> ItemPage[_T]: ...

    @t.overload
    def collect(
        self: SyncPageIterator[RawAPIPageResponse],
    ) -> t.List[RawAPIItem]: ...

    def collect(
        self: t.Union[
            SyncPageIterator[ItemPage[_T]],
            SyncPageIterator[RawAPIPageResponse],
        ],
    ) -> t.Union[ItemPage[_T], t.List[RawAPIItem]]:
        return self.__class__.gather_from_iterator(self)

    @classmethod
    def unix(
        cls,
        method: SyncUnixPaginationMethod[_PageT],
        /,
        *args: t.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        key: str,
        attr: str,
        **kwargs: t.Any,
    ) -> t.Generator[_PageT, None, None]:
        cls._validate_unix_pagination_parameter(method, kwargs, key, attr)
        kwargs["max_items"] = max_items

        current_timestamp = None
        while True:
            pages = list(
                cls._create_unix_timestamp_iterator(
                    method, *args, timestamp=current_timestamp, **kwargs
                )
            )

            if not pages:
                break

            yield from pages

            new_timestamp = cls._extract_unix_timestamp(pages[-1], key, attr)

            if new_timestamp is None or new_timestamp == current_timestamp:
                break

            current_timestamp = new_timestamp

    @t.overload
    @classmethod
    def gather_pages(
        cls,
        method: SyncPaginationMethod[ItemPage[_T]],
        /,
        *args: t.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: t.Literal[False] = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> ItemPage[_T]: ...

    @t.overload
    @classmethod
    def gather_pages(
        cls,
        method: SyncPaginationMethod[RawAPIPageResponse],
        /,
        *args: t.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: t.Literal[False] = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    @classmethod
    def gather_pages(
        cls,
        method: SyncUnixPaginationMethod[ItemPage[_T]],
        /,
        *args: t.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: _OptionalTimestampPaginationConfig = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> ItemPage[_T]: ...

    @t.overload
    @classmethod
    def gather_pages(
        cls,
        method: SyncUnixPaginationMethod[RawAPIPageResponse],
        /,
        *args: t.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: _OptionalTimestampPaginationConfig = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> t.List[RawAPIItem]: ...

    @classmethod
    def gather_pages(
        cls,
        method: t.Union[
            SyncPaginationMethod[t.Union[ItemPage[_T], RawAPIPageResponse]],
            SyncUnixPaginationMethod[
                t.Union[ItemPage[_T], RawAPIPageResponse]
            ],
        ],
        /,
        *args: t.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: _OptionalTimestampPaginationConfig = False,
        return_format: CollectReturnFormat = CollectReturnFormat.FIRST,
        deduplicate: bool = True,
        **kwargs: t.Any,
    ) -> t.Union[ItemPage[_T], t.List[RawAPIItem]]:
        cls._validate_unix_config(unix)
        kwargs["max_items"] = max_items
        if unix is False:
            casted_method = t.cast(
                t.Union[
                    SyncPaginationMethod[_PageT],
                    SyncUnixPaginationMethod[_PageT],
                ],
                method,
            )
            # Type annotation needed as mypy can't infer that
            # both branches return compatible iterable
            iterator: t.Iterator = cls(casted_method, *args, **kwargs)
        else:
            casted_method = t.cast(SyncUnixPaginationMethod[_PageT], method)
            iterator = cls.unix(casted_method, *args, **unix, **kwargs)
        return cls.gather_from_iterator(
            iterator, return_format=return_format, deduplicate=deduplicate
        )

    @t.overload
    @classmethod
    def gather_from_iterator(
        cls,
        iterator: t.Iterator[ItemPage[_T]],
        /,
        *,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
    ) -> ItemPage[_T]: ...

    @t.overload
    @classmethod
    def gather_from_iterator(
        cls,
        iterator: t.Iterator[RawAPIPageResponse],
        /,
        *,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
    ) -> t.List[RawAPIItem]: ...

    @classmethod
    def gather_from_iterator(
        cls,
        iterator: t.Iterator[t.Union[ItemPage[_T], RawAPIPageResponse]],
        /,
        *,
        return_format: CollectReturnFormat = CollectReturnFormat.FIRST,
        deduplicate: bool = True,
    ) -> t.Union[ItemPage[_T], t.List[RawAPIItem]]:
        return cls._process_collected_pages(
            list(t.cast(t.Iterator[_PageT], iterator)),
            return_format,
            deduplicate,
        )


@t.final
class AsyncPageIterator(_BasyAsyncPageIterator[_PageT]):
    __slots__ = ()

    @t.overload
    async def collect(
        self: AsyncPageIterator[ItemPage[_T]],
    ) -> ItemPage[_T]: ...

    @t.overload
    async def collect(
        self: AsyncPageIterator[RawAPIPageResponse],
    ) -> t.List[RawAPIItem]: ...

    async def collect(
        self: t.Union[
            AsyncPageIterator[ItemPage[_T]],
            AsyncPageIterator[RawAPIPageResponse],
        ],
    ) -> t.Union[ItemPage[_T], t.List[RawAPIItem]]:
        return await self.__class__.gather_from_iterator(self)

    @classmethod
    async def unix(
        cls,
        method: AsyncUnixPaginationMethod[_PageT],
        /,
        *args: t.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        key: str,
        attr: str,
        **kwargs: t.Any,
    ) -> t.AsyncGenerator[_PageT, None]:
        cls._validate_unix_pagination_parameter(method, kwargs, key, attr)
        kwargs["max_items"] = max_items

        current_timestamp = None
        while True:
            pages = [
                page
                async for page in cls._create_unix_timestamp_iterator(
                    method, *args, timestamp=current_timestamp, **kwargs
                )
            ]

            if not pages:
                break

            for page in pages:
                yield page

            new_timestamp = cls._extract_unix_timestamp(pages[-1], key, attr)

            if new_timestamp is None or new_timestamp == current_timestamp:
                break

            current_timestamp = new_timestamp

    @t.overload
    @classmethod
    async def gather_pages(
        cls,
        method: AsyncPaginationMethod[ItemPage[_T]],
        /,
        *args: t.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: t.Literal[False] = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> ItemPage[_T]: ...

    @t.overload
    @classmethod
    async def gather_pages(
        cls,
        method: AsyncPaginationMethod[RawAPIPageResponse],
        /,
        *args: t.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: t.Literal[False] = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    @classmethod
    async def gather_pages(
        cls,
        method: AsyncUnixPaginationMethod[ItemPage[_T]],
        /,
        *args: t.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: _OptionalTimestampPaginationConfig = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> ItemPage[_T]: ...

    @t.overload
    @classmethod
    async def gather_pages(
        cls,
        method: AsyncUnixPaginationMethod[RawAPIPageResponse],
        /,
        *args: t.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: _OptionalTimestampPaginationConfig = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> t.List[RawAPIItem]: ...

    @classmethod
    async def gather_pages(
        cls,
        method: t.Union[
            AsyncPaginationMethod[t.Union[ItemPage[_T], RawAPIPageResponse]],
            AsyncUnixPaginationMethod[
                t.Union[ItemPage[_T], RawAPIPageResponse]
            ],
        ],
        /,
        *args: t.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: _OptionalTimestampPaginationConfig = False,
        return_format: CollectReturnFormat = CollectReturnFormat.FIRST,
        deduplicate: bool = True,
        **kwargs: t.Any,
    ) -> t.Union[ItemPage[_T], t.List[RawAPIItem]]:
        cls._validate_unix_config(unix)
        kwargs["max_items"] = max_items
        if unix is False:
            casted_method = t.cast(
                t.Union[
                    AsyncPaginationMethod[_PageT],
                    AsyncUnixPaginationMethod[_PageT],
                ],
                method,
            )
            iterator: t.AsyncIterator = cls(casted_method, *args, **kwargs)
        else:
            casted_method = t.cast(AsyncUnixPaginationMethod[_PageT], method)
            iterator = cls.unix(casted_method, *args, **unix, **kwargs)
        return await cls.gather_from_iterator(
            iterator, return_format=return_format, deduplicate=deduplicate
        )

    @t.overload
    @classmethod
    async def gather_from_iterator(
        cls,
        iterator: t.AsyncIterator[ItemPage[_T]],
        /,
        *,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
    ) -> ItemPage[_T]: ...

    @t.overload
    @classmethod
    async def gather_from_iterator(
        cls,
        iterator: t.AsyncIterator[RawAPIPageResponse],
        /,
        *,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
    ) -> t.List[RawAPIItem]: ...

    @classmethod
    async def gather_from_iterator(
        cls,
        iterator: t.AsyncIterator[t.Union[ItemPage[_T], RawAPIPageResponse]],
        /,
        *,
        return_format: CollectReturnFormat = CollectReturnFormat.FIRST,
        deduplicate: bool = True,
    ) -> t.Union[ItemPage[_T], t.List[RawAPIItem]]:
        return cls._process_collected_pages(
            t.cast(t.List[_PageT], [page async for page in iterator]),
            return_format,
            deduplicate,
        )
