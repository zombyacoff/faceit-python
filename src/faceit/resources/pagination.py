# mypy: disable-error-code="no-any-return"
from __future__ import annotations

import math
import typing
from abc import ABC
from dataclasses import dataclass
from inspect import Parameter, signature
from itertools import chain
from warnings import warn

from annotated_types import Le
from pydantic import PositiveInt
from pydantic.fields import FieldInfo
from typing_extensions import Self, TypeAlias, deprecated

from faceit.constants import RAW_RESPONSE_ITEMS_KEY
from faceit.models import ItemPage
from faceit.models.item_page import PaginationTimeRange
from faceit.types import (
    _T,
    AsyncPaginationMethod,
    AsyncUnixPaginationMethod,
    BaseUnixPaginationMethod,
    PaginationMethodT,
    RawAPIItem,
    RawAPIPageResponse,
    SyncPaginationMethod,
    SyncUnixPaginationMethod,
)
from faceit.utils import (
    StrEnum,
    UnsetValue,
    deduplicate_unhashable,
    deep_get,
    extends,
    representation,
    validate_positive_int,
)

_PageType: TypeAlias = typing.Union[ItemPage[typing.Any], RawAPIPageResponse]
_PageList: TypeAlias = typing.List[_PageType]
_PageT = typing.TypeVar("_PageT", bound=_PageType)


@typing.final
class TimestampPaginationConfig(typing.TypedDict):
    key: str
    attr: str


class CollectReturnFormat(StrEnum):
    FIRST = "first"
    RAW = "raw"
    MODEL = "model"


class MaxItems(StrEnum):
    SAFE = "safe"


# We use `PositiveInt` for Pydantic validation where available (e.g., with
# `@validate_call` in resource methods). However, in this module we implement
# our own validation logic for greater flexibility, as Pydantic-based validation
# is not always practical here.
MaxItemsType: TypeAlias = typing.Union[MaxItems, PositiveInt]

if typing.TYPE_CHECKING:
    _PageClass: TypeAlias = typing.Union[
        typing.Type[ItemPage[typing.Any]], typing.Type[RawAPIPageResponse]
    ]
    _PageFactory: TypeAlias = typing.Callable[[_PageList], _PageClass]
    _PageFactoryMap: TypeAlias = typing.Dict[CollectReturnFormat, _PageFactory]
    _OptionalTimestampPaginationConfig: TypeAlias = typing.Union[
        TimestampPaginationConfig, typing.Literal[False]
    ]


@typing.final
class PaginationMaxParams(typing.NamedTuple):
    limit: int
    offset: int


@typing.final
class pages(int):  # noqa: N801
    __slots__ = ()

    @extends(int.__new__)
    def __new__(cls, x: typing.Any = 2, base: typing.Any = None) -> typing.Any:
        integer = super().__new__(cls, *(x,) if base is None else (x, base))
        if integer > 1:
            return integer
        raise ValueError(
            f"Invalid value for {cls.__name__}: {integer!r}. "
            "Expected a positive integer greater than 1."
        )


@typing.final
@deprecated(
    "`MaxPages` is deprecated and will be removed in a future release. Use `pages` instead."
)
class MaxPages(pages):  # type: ignore[misc]
    __slots__ = ()


@dataclass(eq=False, frozen=True)
class _MethodCall(typing.Generic[PaginationMethodT]):
    call: PaginationMethodT
    args: typing.Tuple[typing.Any, ...]
    kwargs: typing.Dict[str, typing.Any]


class _MaxItemsInfo(typing.NamedTuple):
    max_items: MaxItemsType
    last_page_remainder: int
    is_partial_last_page: bool

    @classmethod
    def from_max_pages(cls, max_pages: MaxItemsType, /) -> Self:
        return cls(max_pages, 0, False)


_UNIX_METHOD_REQUIRED_KEYS: typing.Final = frozenset(TimestampPaginationConfig.__annotations__)  # fmt: skip
_PAGINATION_ARGS: typing.Final = PaginationMaxParams._fields
_UNIX_PAGINATION_PARAMS: typing.Final = PaginationTimeRange._fields


def _has_unix_pagination_params(method: BaseUnixPaginationMethod[typing.Any], /) -> bool:  # fmt: skip
    return all(param in signature(method).parameters for param in _UNIX_PAGINATION_PARAMS)  # fmt: skip


def _get_le(param: Parameter, /) -> typing.Optional[Le]:
    return next((items for items in param.default.metadata if isinstance(items, Le)), None)  # fmt: skip


def _extract_pagination_limits(
    limit_param: Parameter, offset_param: Parameter, method_name: str, /
) -> PaginationMaxParams:
    # Validates pagination parameters for:
    # 1. Development - ensures correct function signatures with clear error messages
    # 2. Static typing - enables mypy to verify type correctness
    if limit_param.default is None or offset_param.default is None:
        raise ValueError(
            f"Function {method_name!r} missing default value for limit/offset parameter"
        )
    if not isinstance(limit_param.default, FieldInfo) or not isinstance(
        offset_param.default, FieldInfo
    ):
        raise TypeError(
            f"Default for limit/offset in {method_name!r} is not a FieldInfo"
        )
    limit_constraint = _get_le(limit_param)
    if limit_constraint is None:
        raise ValueError(
            f"In limit metadata of {method_name!r}, no Le constraint found"
        )
    offset_constraint = _get_le(offset_param)
    return PaginationMaxParams(
        validate_positive_int(limit_constraint.le),
        UnsetValue.UNSET
        if offset_constraint is None
        else validate_positive_int(offset_constraint.le),
    )


def check_pagination_support(
    func: typing.Callable[..., typing.Any], /
) -> typing.Union[PaginationMaxParams, typing.Literal[False]]:
    # Imported here to avoid circular dependency: `base` imports iterators and config
    # to integrate them into `BaseResource` for convenient use in subclasses.
    from .base import BaseResource  # noqa: PLC0415

    if not hasattr(func, "__self__") or not issubclass(
        func.__self__.__class__, BaseResource
    ):
        return False

    limit_param, offset_param = (
        signature(func).parameters.get(arg) for arg in _PAGINATION_ARGS
    )

    if limit_param is None or offset_param is None:
        return False

    return _extract_pagination_limits(limit_param, offset_param, func.__name__)


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
class BasePageIterator(ABC, typing.Generic[PaginationMethodT, _PageT]):
    __slots__ = _ITERATOR_SLOTS

    if typing.TYPE_CHECKING:
        _STOP_ITERATION_EXC: typing.ClassVar[typing.Type[Exception]]

    _COLLECT_RETURN_FORMATS: typing.ClassVar[_PageFactoryMap] = {
        CollectReturnFormat.FIRST: lambda c: type(c[0]) if c else RawAPIPageResponse,
        CollectReturnFormat.RAW: lambda _: RawAPIPageResponse,
        CollectReturnFormat.MODEL: lambda _: ItemPage,
    }

    SAFE_MAX_PAGES: typing.ClassVar = 100
    DEFAULT_MAX_ITEMS: typing.ClassVar = 2000
    """
    Selected as an optimal default to balance performance and resource usage
    when iterating through paginated FACEIT API data.
    """

    timestamp_cfg: typing.ClassVar = TimestampPaginationConfig

    def __init__(
        self,
        method: PaginationMethodT,
        /,
        *args: typing.Any,
        max_items: MaxItemsType = DEFAULT_MAX_ITEMS,
        **kwargs: typing.Any,
    ) -> None:
        pagination_limits = check_pagination_support(method)
        if pagination_limits is False:
            raise ValueError(
                f"Method {method.__name__!r} does not support pagination. "
                "Ensure it's a BaseResource method with offset and limit parameters."
            )
        self._method = _MethodCall[PaginationMethodT](
            method, args, self.__class__._remove_pagination_args(**kwargs)
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
        return (
            self._max_items_info.max_items * self._pagination_limits.limit
            if isinstance(self._max_items_info.max_items, pages)
            else int(self._max_items_info.max_items)
        )

    @max_items.setter
    def max_items(self, value: MaxItemsType) -> None:
        self._max_pages_setter(value)

    @property
    def exhausted(self) -> bool:
        return self._exhausted

    @property
    def current_offset(self) -> int:
        return self._offset

    @current_offset.setter
    def current_offset(self, value: int) -> None:
        validate_positive_int(value, param_name="offset")
        if self._exhausted:
            raise ValueError(
                "Pagination offset cannot be set after the iterator has been exhausted."
            )
        if value > self._pagination_limits.limit:
            raise ValueError(
                "Pagination offset cannot exceed the maximum limit "
                f"({self._pagination_limits.limit}): {value}."
            )
        self._offset = value

    @property
    def current_page_index(self) -> int:
        return self._page_index

    @property
    def supports_unix_params(self) -> bool:
        return _has_unix_pagination_params(self._method.call)

    @property
    def _effective_limit(self) -> int:
        """
        Returns an effective limit for the last page to ensure the offset
        is a multiple of the limit, as required by the API
        ("400 Bad pagination request: 'offset' must be a multiple of 'limit'").
        """
        if not (
            self._max_items_info.is_partial_last_page
            and self._page_index == self._max_pages - 1
        ):
            return self._pagination_limits.limit
        return next(
            (
                possible_limit
                for possible_limit in range(
                    self._max_items_info.last_page_remainder,
                    self._pagination_limits.limit + 1,
                )
                if self._offset % possible_limit == 0
            ),
            self._max_items_info.last_page_remainder,
        )

    def reset(self) -> None:
        self._init_iteration()

    def with_updated_args(self, *args: typing.Any, **kwargs: typing.Any) -> Self:
        return self.__class__(self._method.call, *args, **kwargs)

    def _max_pages_setter(self, max_items: MaxItemsType, /) -> None:
        def set_max_pages(max_pages: int, /) -> None:
            self._max_pages = max_pages
            self._max_items_info = _MaxItemsInfo.from_max_pages(max_pages)

        def warn_if_exceeds_safe(max_pages: int, /) -> int:
            if max_pages > self.__class__.SAFE_MAX_PAGES:
                warn(
                    f"The computed number of pages ({max_pages}) exceeds the "
                    f"recommended safe maximum ({self.__class__.SAFE_MAX_PAGES}). "
                    "Proceed at your own risk.",
                    UserWarning,
                    stacklevel=2,
                )
            return max_pages

        if max_items == MaxItems.SAFE:
            set_max_pages(self.__class__.SAFE_MAX_PAGES)
            return

        if isinstance(max_items, pages):
            set_max_pages(warn_if_exceeds_safe(max_items))
            return

        validate_positive_int(max_items, param_name="max_items")
        last_page_remainder = max_items % self._pagination_limits.limit
        self._max_items_info = _MaxItemsInfo(
            max_items, last_page_remainder, last_page_remainder != 0
        )
        self._max_pages = warn_if_exceeds_safe(
            math.ceil(max_items / self._pagination_limits.limit)
        )

    def _handle_iteration_state(self, page: typing.Optional[_PageT], /) -> _PageT:
        if page is None:
            self._exhausted = True
            raise self.__class__._STOP_ITERATION_EXC

        self._page_index += 1

        is_page_smaller_than_limit = (
            len(page[RAW_RESPONSE_ITEMS_KEY] if isinstance(page, dict) else page)
            < self._pagination_limits.limit
        )

        is_offset_exceeded = (
            self._pagination_limits.offset != UnsetValue.UNSET
            and self._offset >= self._pagination_limits.offset
        )

        is_max_items_reached = self._page_index >= self._max_pages
        if is_max_items_reached and self._max_items_info.is_partial_last_page:
            # Considering post-filtering extra items on the last page when the limit
            # is increased due to offset/limit constraints (see `_effective_limit`).
            # For now, we leave this to the user and warn that the response may
            # contain more items than requested in such cases.
            pass

        self._exhausted = (
            is_page_smaller_than_limit or is_offset_exceeded or is_max_items_reached
        )

        self._offset += self._pagination_limits.limit
        return page

    @staticmethod
    def _remove_pagination_args(**kwargs: _T) -> typing.Dict[str, _T]:
        if any(kwargs.pop(arg, None) for arg in _PAGINATION_ARGS):
            warn(
                f"Pagination parameters {_PAGINATION_ARGS} should not be "
                "provided by users. These parameters are managed internally "
                "by the pagination system.",
                UserWarning,
                stacklevel=2,
            )
        return kwargs

    @staticmethod
    def _validate_unix_pagination_parameter(
        method: PaginationMethodT,
        # Process `kwargs` to filter pagination parameters and issue warnings
        # when user-provided values will be ignored
        kwargs: typing.Dict[str, typing.Any],
        key: str,
        attr: str,
    ) -> None:
        if not _has_unix_pagination_params(method):
            raise ValueError(
                f"Method {method.__name__!r} does not appear to support Unix timestamp "
                "pagination. Expected start and to parameters."
            )
        if any(not isinstance(value, str) or not value for value in (key, attr)):
            raise ValueError(
                f"Key and attribute parameters must be non-empty strings: {key}, {attr}."
            )
        if any(kwargs.pop(arg, None) for arg in _UNIX_PAGINATION_PARAMS):
            warn(
                "The parameters start and to will be managed automatically with Unix "
                "timestamp pagination. Your provided values will be ignored.",
                UserWarning,
                stacklevel=3,
            )

    @staticmethod
    def _validate_unix_config(
        unix_config: _OptionalTimestampPaginationConfig, /
    ) -> None:
        if unix_config is not False and not isinstance(unix_config, dict):
            raise ValueError(
                "Invalid unix pagination configuration: expected UnixPaginationConfig "
                f"dictionary or False, got {type(unix_config).__name__}. "
                "See pagination.UnixPaginationConfig for the required format."
            )
        if (
            isinstance(unix_config, dict)
            and _UNIX_METHOD_REQUIRED_KEYS - unix_config.keys()
        ):
            raise ValueError(
                "Invalid unix pagination configuration: "
                f"missing required keys {tuple(_UNIX_METHOD_REQUIRED_KEYS)}. "
                "See pagination.UnixPaginationConfig for the required format."
            )

    @staticmethod
    def _extract_unix_timestamp(
        page: typing.Optional[_PageT], key: str, attr: str, /
    ) -> typing.Optional[int]:
        if not page:
            return None
        return (
            deep_get(page[RAW_RESPONSE_ITEMS_KEY][-1], key)
            if isinstance(page, dict)
            else getattr(page.last(), attr, None)
        )

    @staticmethod
    def _filter_collection(
        collection: typing.List[_PageT],
        expected_type: typing.Type[typing.Any],
        /,
    ) -> typing.List[typing.Any]:
        return [item for item in collection if isinstance(item, expected_type)]

    @staticmethod
    def _extract_items_from_raw_pages(
        pages: typing.List[RawAPIPageResponse], /
    ) -> typing.List[RawAPIItem]:
        return list(chain.from_iterable(page[RAW_RESPONSE_ITEMS_KEY] for page in pages))

    @classmethod
    def _process_collected_pages(
        cls,
        collection: typing.List[_PageT],
        return_format: CollectReturnFormat,
        deduplicate: bool,
        /,
    ) -> typing.Union[ItemPage[_T], typing.List[RawAPIItem]]:
        is_raw_mode = (
            cls._COLLECT_RETURN_FORMATS[return_format](
                typing.cast("_PageList", collection)
            )
            is dict
        )
        filtered = cls._filter_collection(collection, dict if is_raw_mode else ItemPage)
        processed = (
            cls._extract_items_from_raw_pages(filtered)
            if is_raw_mode
            else ItemPage.merge(filtered)
        )
        return cls._deduplicate_collection(processed) if deduplicate else processed

    @classmethod
    def _deduplicate_collection(
        cls,
        collection: typing.Union[ItemPage[typing.Any], typing.List[RawAPIItem]],
        /,
    ) -> typing.Union[ItemPage[typing.Any], typing.List[RawAPIItem]]:
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
        *args: typing.Any,
        timestamp: typing.Optional[int],
        **kwargs: typing.Any,
    ) -> Self:
        # fmt: off
        return cls(method, *args, **{
            **kwargs, **({} if timestamp is None else {"to": timestamp + 1}),
        })
        # fmt: on


del _ITERATOR_SLOTS


class _BaseSyncPageIterator(
    BasePageIterator[
        typing.Union[SyncPaginationMethod[_PageT], SyncUnixPaginationMethod[_PageT]],
        _PageT,
    ],
    typing.Iterator[_PageT],
):
    __slots__ = ()

    _STOP_ITERATION_EXC: typing.ClassVar = StopIteration

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> _PageT:
        if self._exhausted:
            raise self.__class__._STOP_ITERATION_EXC
        return self._handle_iteration_state(
            self._method.call(
                *self._method.args,
                **self._method.kwargs,
                limit=self._effective_limit,
                offset=self._offset,
            )
            or None
        )


class _BasyAsyncPageIterator(
    BasePageIterator[
        typing.Union[AsyncPaginationMethod[_PageT], AsyncUnixPaginationMethod[_PageT]],
        _PageT,
    ],
    typing.AsyncIterator[_PageT],
):
    __slots__ = ()

    _STOP_ITERATION_EXC: typing.ClassVar = StopAsyncIteration

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> _PageT:
        if self._exhausted:
            raise self.__class__._STOP_ITERATION_EXC
        return self._handle_iteration_state(
            await self._method.call(
                *self._method.args,
                **self._method.kwargs,
                limit=self._effective_limit,
                offset=self._offset,
            )
            or None
        )


@typing.final
class SyncPageIterator(_BaseSyncPageIterator[_PageT]):
    __slots__ = ()

    @typing.overload
    def collect(
        self: SyncPageIterator[ItemPage[_T]],
    ) -> ItemPage[_T]: ...

    @typing.overload
    def collect(
        self: SyncPageIterator[RawAPIPageResponse],
    ) -> typing.List[RawAPIItem]: ...

    def collect(
        self: typing.Union[
            SyncPageIterator[ItemPage[_T]],
            SyncPageIterator[RawAPIPageResponse],
        ],
    ) -> typing.Union[ItemPage[_T], typing.List[RawAPIItem]]:
        return self.__class__.gather_from_iterator(self)

    @classmethod
    def unix(
        cls,
        method: SyncUnixPaginationMethod[_PageT],
        /,
        *args: typing.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        key: str,
        attr: str,
        **kwargs: typing.Any,
    ) -> typing.Generator[_PageT, None, None]:
        cls._validate_unix_pagination_parameter(method, kwargs, key, attr)
        kwargs["max_items"] = max_items

        current_timestamp = None
        total_yielded = 0

        while True:
            iterator = cls._create_unix_timestamp_iterator(
                method, *args, timestamp=current_timestamp, **kwargs
            )
            pages = list(iterator)

            for page in pages:
                if total_yielded >= iterator.max_items:
                    return
                yield page
                total_yielded += iterator._effective_limit

            if not pages or total_yielded >= iterator.max_items:
                break

            new_timestamp = cls._extract_unix_timestamp(pages[-1], key, attr)
            if new_timestamp is None or new_timestamp == current_timestamp:
                break
            current_timestamp = new_timestamp

            kwargs["max_items"] = iterator.max_items - total_yielded

    @typing.overload
    @classmethod
    def gather_pages(
        cls,
        method: SyncPaginationMethod[ItemPage[_T]],
        /,
        *args: typing.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: typing.Literal[False] = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: typing.Any,
    ) -> ItemPage[_T]: ...

    @typing.overload
    @classmethod
    def gather_pages(
        cls,
        method: SyncPaginationMethod[RawAPIPageResponse],
        /,
        *args: typing.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: typing.Literal[False] = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: typing.Any,
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    @classmethod
    def gather_pages(
        cls,
        method: SyncUnixPaginationMethod[ItemPage[_T]],
        /,
        *args: typing.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: _OptionalTimestampPaginationConfig = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: typing.Any,
    ) -> ItemPage[_T]: ...

    @typing.overload
    @classmethod
    def gather_pages(
        cls,
        method: SyncUnixPaginationMethod[RawAPIPageResponse],
        /,
        *args: typing.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: _OptionalTimestampPaginationConfig = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: typing.Any,
    ) -> typing.List[RawAPIItem]: ...

    @classmethod
    def gather_pages(
        cls,
        method: typing.Union[
            SyncPaginationMethod[typing.Union[ItemPage[_T], RawAPIPageResponse]],
            SyncUnixPaginationMethod[typing.Union[ItemPage[_T], RawAPIPageResponse]],
        ],
        /,
        *args: typing.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: _OptionalTimestampPaginationConfig = False,
        return_format: CollectReturnFormat = CollectReturnFormat.FIRST,
        deduplicate: bool = True,
        **kwargs: typing.Any,
    ) -> typing.Union[ItemPage[_T], typing.List[RawAPIItem]]:
        cls._validate_unix_config(unix)
        kwargs["max_items"] = max_items
        if unix is False:
            casted_method = typing.cast(
                "typing.Union[SyncPaginationMethod[_PageT], SyncUnixPaginationMethod[_PageT]]",
                method,
            )
            # Type annotation needed as mypy can't infer that
            # both branches return compatible iterable
            iterator: typing.Iterator[typing.Any] = cls(casted_method, *args, **kwargs)
        else:
            casted_method = typing.cast("SyncUnixPaginationMethod[_PageT]", method)
            iterator = cls.unix(casted_method, *args, **unix, **kwargs)
        return cls.gather_from_iterator(
            iterator, return_format, deduplicate=deduplicate
        )

    @typing.overload
    @classmethod
    def gather_from_iterator(
        cls,
        iterator: typing.Iterator[ItemPage[_T]],
        /,
        return_format: CollectReturnFormat = ...,
        *,
        deduplicate: bool = ...,
    ) -> ItemPage[_T]: ...

    @typing.overload
    @classmethod
    def gather_from_iterator(
        cls,
        iterator: typing.Iterator[RawAPIPageResponse],
        /,
        return_format: CollectReturnFormat = ...,
        *,
        deduplicate: bool = ...,
    ) -> typing.List[RawAPIItem]: ...

    @classmethod
    def gather_from_iterator(
        cls,
        iterator: typing.Iterator[typing.Union[ItemPage[_T], RawAPIPageResponse]],
        /,
        return_format: CollectReturnFormat = CollectReturnFormat.FIRST,
        *,
        deduplicate: bool = True,
    ) -> typing.Union[ItemPage[_T], typing.List[RawAPIItem]]:
        return cls._process_collected_pages(
            list(typing.cast("typing.Iterator[_PageT]", iterator)),
            return_format,
            deduplicate,
        )


@typing.final
class AsyncPageIterator(_BasyAsyncPageIterator[_PageT]):
    __slots__ = ()

    @typing.overload
    async def collect(
        self: AsyncPageIterator[ItemPage[_T]],
    ) -> ItemPage[_T]: ...

    @typing.overload
    async def collect(
        self: AsyncPageIterator[RawAPIPageResponse],
    ) -> typing.List[RawAPIItem]: ...

    async def collect(
        self: typing.Union[
            AsyncPageIterator[ItemPage[_T]],
            AsyncPageIterator[RawAPIPageResponse],
        ],
    ) -> typing.Union[ItemPage[_T], typing.List[RawAPIItem]]:
        return await self.__class__.gather_from_iterator(self)

    @classmethod
    async def unix(
        cls,
        method: AsyncUnixPaginationMethod[_PageT],
        /,
        *args: typing.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        key: str,
        attr: str,
        **kwargs: typing.Any,
    ) -> typing.AsyncGenerator[_PageT, None]:
        cls._validate_unix_pagination_parameter(method, kwargs, key, attr)
        kwargs["max_items"] = max_items

        current_timestamp = None
        total_yielded = 0

        while True:
            iterator = cls._create_unix_timestamp_iterator(
                method, *args, timestamp=current_timestamp, **kwargs
            )
            pages = [page async for page in iterator]

            for page in pages:
                if total_yielded >= iterator.max_items:
                    return
                yield page
                total_yielded += iterator._effective_limit

            if not pages or total_yielded >= iterator.max_items:
                break

            new_timestamp = cls._extract_unix_timestamp(pages[-1], key, attr)
            if new_timestamp is None or new_timestamp == current_timestamp:
                break
            current_timestamp = new_timestamp

            kwargs["max_items"] = iterator.max_items - total_yielded

    @typing.overload
    @classmethod
    async def gather_pages(
        cls,
        method: AsyncPaginationMethod[ItemPage[_T]],
        /,
        *args: typing.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: typing.Literal[False] = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: typing.Any,
    ) -> ItemPage[_T]: ...

    @typing.overload
    @classmethod
    async def gather_pages(
        cls,
        method: AsyncPaginationMethod[RawAPIPageResponse],
        /,
        *args: typing.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: typing.Literal[False] = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: typing.Any,
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    @classmethod
    async def gather_pages(
        cls,
        method: AsyncUnixPaginationMethod[ItemPage[_T]],
        /,
        *args: typing.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: _OptionalTimestampPaginationConfig = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: typing.Any,
    ) -> ItemPage[_T]: ...

    @typing.overload
    @classmethod
    async def gather_pages(
        cls,
        method: AsyncUnixPaginationMethod[RawAPIPageResponse],
        /,
        *args: typing.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: _OptionalTimestampPaginationConfig = ...,
        return_format: CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: typing.Any,
    ) -> typing.List[RawAPIItem]: ...

    @classmethod
    async def gather_pages(
        cls,
        method: typing.Union[
            AsyncPaginationMethod[typing.Union[ItemPage[_T], RawAPIPageResponse]],
            AsyncUnixPaginationMethod[typing.Union[ItemPage[_T], RawAPIPageResponse]],
        ],
        /,
        *args: typing.Any,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        unix: _OptionalTimestampPaginationConfig = False,
        return_format: CollectReturnFormat = CollectReturnFormat.FIRST,
        deduplicate: bool = True,
        **kwargs: typing.Any,
    ) -> typing.Union[ItemPage[_T], typing.List[RawAPIItem]]:
        cls._validate_unix_config(unix)
        kwargs["max_items"] = max_items
        if unix is False:
            casted_method = typing.cast(
                "typing.Union[AsyncPaginationMethod[_PageT], AsyncUnixPaginationMethod[_PageT]]",
                method,
            )
            iterator: typing.AsyncIterator[typing.Any] = cls(
                casted_method, *args, **kwargs
            )
        else:
            casted_method = typing.cast("AsyncUnixPaginationMethod[_PageT]", method)
            iterator = cls.unix(casted_method, *args, **unix, **kwargs)
        return await cls.gather_from_iterator(
            iterator, return_format, deduplicate=deduplicate
        )

    @typing.overload
    @classmethod
    async def gather_from_iterator(
        cls,
        iterator: typing.AsyncIterator[ItemPage[_T]],
        /,
        return_format: CollectReturnFormat = ...,
        *,
        deduplicate: bool = ...,
    ) -> ItemPage[_T]: ...

    @typing.overload
    @classmethod
    async def gather_from_iterator(
        cls,
        iterator: typing.AsyncIterator[RawAPIPageResponse],
        /,
        return_format: CollectReturnFormat = ...,
        *,
        deduplicate: bool = ...,
    ) -> typing.List[RawAPIItem]: ...

    @classmethod
    async def gather_from_iterator(
        cls,
        iterator: typing.AsyncIterator[typing.Union[ItemPage[_T], RawAPIPageResponse]],
        /,
        return_format: CollectReturnFormat = CollectReturnFormat.FIRST,
        *,
        deduplicate: bool = True,
    ) -> typing.Union[ItemPage[_T], typing.List[RawAPIItem]]:
        return cls._process_collected_pages(
            typing.cast("typing.List[_PageT]", [page async for page in iterator]),
            return_format,
            deduplicate,
        )
