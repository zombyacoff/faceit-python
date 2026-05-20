from __future__ import annotations

import inspect
import math
import warnings
from abc import ABC
from collections.abc import AsyncIterator, Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from itertools import chain
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Final,
    Generic,
    Literal,
    NamedTuple,
    TypeAlias,
    TypedDict,
    TypeVar,
    cast,
    final,
    overload,
)

from annotated_types import Le
from pydantic.fields import FieldInfo
from typing_extensions import Self

from faceit.constants import RAW_RESPONSE_ITEMS_KEY
from faceit.models import ItemPage
from faceit.models.item_page import PaginationTimeRange
from faceit.types import (
    _T,
    AsyncResourceMethodProtocol,
    BaseResourceMethodProtocol,
    PaginationMethodT,
    RawAPIItem,
    RawAPIPageResponse,
    SyncResourceMethodProtocol,
)
from faceit.utils import (
    StrEnum,
    deduplicate_unhashable,
    deep_get,
    extends,
    find_user_stacklevel,
    representation,
    validate_positive_int,
)

ProcessedPages: TypeAlias = list[RawAPIItem] | ItemPage[_T]
_PageType: TypeAlias = RawAPIPageResponse | ItemPage[_T]
_PageList: TypeAlias = list[_PageType[_T]]
_PageT = TypeVar("_PageT", bound=_PageType[Any])


if TYPE_CHECKING:
    _PageFactoryMap: TypeAlias = Mapping[
        "CollectReturnFormat",
        Callable[[_PageList[Any]], type[RawAPIPageResponse | ItemPage[Any]]],
    ]
    _OptionalTimestampPaginationConfig: TypeAlias = (
        "TimestampPaginationConfig | Literal[False]"
    )


class MaxItems(StrEnum):
    SAFE = "safe"


MaxItemsType: TypeAlias = MaxItems | int


class CollectReturnFormat(StrEnum):
    FIRST = "first"
    RAW = "raw"
    MODEL = "model"


@final
class TimestampPaginationConfig(TypedDict):
    key: str
    attr: str


@final
class PaginationMaxParams(NamedTuple):
    limit: int
    offset: int | None


@final
class pages(int):
    __slots__ = ()

    @extends(int.__new__)
    def __new__(cls, x=2, base=None):  # type: ignore[no-untyped-def] # noqa: ANN001, ANN204
        integer = super().__new__(cls, *(x,) if base is None else (x, base))
        if integer > 1:
            return integer
        msg = (
            f"Invalid value for {cls.__name__}: {integer!r}. "
            "Expected a positive integer greater than 1."
        )
        raise ValueError(msg)


@dataclass(eq=False, frozen=True)
class _MethodCall(Generic[PaginationMethodT]):
    call: PaginationMethodT
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


class _MaxItemsInfo(NamedTuple):
    max_items: MaxItemsType
    last_page_remainder: int
    is_partial_last_page: bool

    @classmethod
    def from_max_pages(cls, max_pages: MaxItemsType, /) -> Self:
        return cls(max_pages, 0, is_partial_last_page=False)


_UNIX_METHOD_REQUIRED_KEYS: Final = frozenset(TimestampPaginationConfig.__annotations__)
_PAGINATION_ARGS: Final = PaginationMaxParams._fields
_UNIX_PAGINATION_PARAMS: Final = PaginationTimeRange.model_fields.keys()


def _has_unix_pagination_params(method: BaseResourceMethodProtocol[Any], /) -> bool:
    return all(
        param in inspect.signature(method).parameters
        for param in _UNIX_PAGINATION_PARAMS
    )


def _get_le(param: inspect.Parameter, /) -> Le | None:
    generator = (items for items in param.default.metadata if isinstance(items, Le))
    return next(generator, None)


def _extract_pagination_limits(
    limit_param: inspect.Parameter, offset_param: inspect.Parameter, method_name: str, /
) -> PaginationMaxParams:
    # Validates pagination parameters for:
    # 1. Development - ensures correct function signatures with clear error messages
    # 2. Static typing - enables mypy to verify type correctness
    if limit_param.default is None or offset_param.default is None:
        msg = (
            f"Function {method_name!r} missing default value for limit/offset parameter"
        )
        raise ValueError(msg)
    if not isinstance(limit_param.default, FieldInfo) or not isinstance(
        offset_param.default, FieldInfo
    ):
        msg = f"Default for limit/offset in {method_name!r} is not a FieldInfo"
        raise TypeError(msg)
    limit_constraint = _get_le(limit_param)
    if limit_constraint is None:
        msg = f"In limit metadata of {method_name!r}, no Le constraint found"
        raise ValueError(msg)
    offset_constraint = _get_le(offset_param)
    offset = (
        None
        if offset_constraint is None
        else validate_positive_int(offset_constraint.le)
    )
    return PaginationMaxParams(validate_positive_int(limit_constraint.le), offset)


def check_pagination_support(
    func: Callable[..., Any], /
) -> PaginationMaxParams | Literal[False]:
    # Imported here to avoid circular dependency: `base` imports iterators and config
    # to integrate them into `BaseResource` for convenient use in subclasses.
    from faceit.api.base import BaseResource  # noqa: PLC0415

    if not hasattr(func, "__self__") or not issubclass(
        func.__self__.__class__,  # pyright: ignore[reportFunctionMemberAccess]
        BaseResource,
    ):
        return False

    limit_param, offset_param = (
        inspect.signature(func).parameters.get(arg) for arg in _PAGINATION_ARGS
    )

    if limit_param is None or offset_param is None:
        return False

    return _extract_pagination_limits(
        limit_param, offset_param, cast("str", getattr(func, "__name__", "<unknown>"))
    )


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
class BasePageIterator(ABC, Generic[PaginationMethodT, _PageT]):
    __slots__ = _ITERATOR_SLOTS

    if TYPE_CHECKING:
        _STOP_ITERATION_EXC: ClassVar[type[Exception]]

    _COLLECT_RETURN_FORMATS: ClassVar[_PageFactoryMap] = MappingProxyType({
        CollectReturnFormat.FIRST: lambda c: type(c[0]) if c else RawAPIPageResponse,
        CollectReturnFormat.RAW: lambda _: RawAPIPageResponse,
        CollectReturnFormat.MODEL: lambda _: ItemPage,
    })

    SAFE_MAX_PAGES: ClassVar = 100
    DEFAULT_MAX_ITEMS: ClassVar = 2000
    """
    Selected as an optimal default to balance performance and resource usage
    when iterating through paginated FACEIT API data.
    """

    def __init__(
        self,
        method: PaginationMethodT,
        /,
        *args: Any,
        max_items: MaxItemsType = DEFAULT_MAX_ITEMS,
        **kwargs: Any,
    ) -> None:
        pagination_limits = check_pagination_support(method)
        if pagination_limits is False:
            msg = (
                f"Method {method.__name__!r} does not support pagination. "
                "Ensure it's a BaseResource method with offset and limit parameters."
            )
            raise ValueError(msg)
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
    def max_items(self, value: MaxItemsType, /) -> None:
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
            msg = (
                "Pagination offset cannot be set after the iterator has been exhausted."
            )
            raise ValueError(msg)
        if value > self._pagination_limits.limit:
            msg = (
                "Pagination offset cannot exceed the maximum limit "
                f"({self._pagination_limits.limit}): {value}."
            )
            raise ValueError(msg)
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

    def with_updated_args(self, *args: Any, **kwargs: Any) -> Self:
        return self.__class__(self._method.call, *args, **kwargs)

    def _max_pages_setter(self, max_items: MaxItemsType, /) -> None:
        def set_max_pages(max_pages: int, /) -> None:
            self._max_pages = max_pages
            self._max_items_info = _MaxItemsInfo.from_max_pages(max_pages)

        def warn_if_exceeds_safe(max_pages: int, /) -> int:
            if max_pages > self.__class__.SAFE_MAX_PAGES:
                warnings.warn(
                    f"The computed number of pages ({max_pages}) exceeds the "
                    f"recommended safe maximum ({self.__class__.SAFE_MAX_PAGES}). "
                    "Proceed at your own risk.",
                    stacklevel=find_user_stacklevel(),
                )
            return max_pages

        if max_items == MaxItems.SAFE:
            set_max_pages(self.__class__.SAFE_MAX_PAGES)
            return

        if isinstance(max_items, pages):
            set_max_pages(warn_if_exceeds_safe(max_items))
            return

        validated_max_items = validate_positive_int(max_items, param_name="max_items")
        last_page_remainder = validated_max_items % self._pagination_limits.limit
        self._max_items_info = _MaxItemsInfo(
            validated_max_items, last_page_remainder, last_page_remainder != 0
        )
        self._max_pages = warn_if_exceeds_safe(
            math.ceil(validated_max_items / self._pagination_limits.limit)
        )

    def _handle_iteration_state(self, page: _PageT | None, /) -> _PageT:
        if page is None:
            self._exhausted = True
            raise self.__class__._STOP_ITERATION_EXC

        self._page_index += 1

        is_page_smaller_than_limit = (
            len(page[RAW_RESPONSE_ITEMS_KEY] if isinstance(page, dict) else page)
            < self._pagination_limits.limit
        )

        is_offset_exceeded = (
            self._pagination_limits.offset is not None
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
    def _remove_pagination_args(**kwargs: _T) -> dict[str, _T]:
        if any([kwargs.pop(arg, None) for arg in _PAGINATION_ARGS]):  # noqa: C419
            warnings.warn(
                f"Pagination parameters {_PAGINATION_ARGS} should not be "
                "provided by users. These parameters are managed internally "
                "by the pagination system.",
                stacklevel=find_user_stacklevel(),
            )
        return kwargs

    @staticmethod
    def _validate_unix_config(
        unix_config: _OptionalTimestampPaginationConfig, /
    ) -> None:
        if unix_config is not False and not isinstance(unix_config, dict):
            msg = (  # type: ignore[unreachable]
                "Invalid unix pagination configuration: expected TimestampPaginationConfig "
                f"dictionary or False, got {type(unix_config).__name__}. "
                "See pagination.TimestampPaginationConfig for the required format."
            )
            raise ValueError(msg)
        if (
            isinstance(unix_config, dict)
            and _UNIX_METHOD_REQUIRED_KEYS - unix_config.keys()
        ):
            msg = (
                "Invalid unix pagination configuration: "
                f"missing required keys {tuple(_UNIX_METHOD_REQUIRED_KEYS)}. "
                "See pagination.TimestampPaginationConfig for the required format."
            )
            raise ValueError(msg)

    @staticmethod
    def _extract_unix_timestamp(
        cfg: TimestampPaginationConfig, page: _PageType[Any] | None, /
    ) -> int | None:
        if not page:
            return None
        if isinstance(page, dict):
            items = page.get(RAW_RESPONSE_ITEMS_KEY) or []
            return deep_get(items[-1], cfg["key"]) if items else None
        return getattr(page.get_last(), cfg["attr"], None)

    @classmethod
    def _validate_unix_pagination_parameter(
        cls,
        cfg: TimestampPaginationConfig,
        method: PaginationMethodT,
        # Process `kwargs` to filter pagination parameters and issue warnings
        # when user-provided values will be ignored
        kwargs: dict[str, Any],
        /,
    ) -> None:
        cls._validate_unix_config(cfg)
        if not _has_unix_pagination_params(method):
            msg = (
                f"Method {method.__name__!r} does not appear to support Unix timestamp pagination. "
                "Expected 'start' and 'to' parameters."
            )
            raise ValueError(msg)
        if any(
            not isinstance(value, str) or not value
            for value in (cfg["key"], cfg["attr"])
        ):
            msg = f"Key and attribute parameters must be non-empty strings: {cfg['key']}, {cfg['attr']}."
            raise ValueError(msg)
        if any(kwargs.pop(arg, None) for arg in _UNIX_PAGINATION_PARAMS):
            warnings.warn(
                "The parameters 'start' and 'to' will be managed automatically with Unix "
                "timestamp pagination. Your provided values will be ignored.",
                stacklevel=find_user_stacklevel(),
            )

    @classmethod
    def _process_collected_pages(
        cls,
        collection: _PageList[_T],
        return_format: CollectReturnFormat,
        deduplicate: bool,  # noqa: FBT001
    ) -> ProcessedPages[_T]:
        if cls._COLLECT_RETURN_FORMATS[return_format](collection) is dict:
            raw = chain.from_iterable(
                p[RAW_RESPONSE_ITEMS_KEY] for p in collection if isinstance(p, dict)
            )
            return cls._deduplicate_collection(raw) if deduplicate else list(raw)
        model = ItemPage.merge(p for p in collection if isinstance(p, ItemPage))
        return cls._deduplicate_collection(model) if deduplicate else model

    @classmethod
    def _deduplicate_collection(
        cls, collection: Iterable[RawAPIItem] | ItemPage[_T], /
    ) -> ProcessedPages[_T]:
        if not isinstance(collection, ItemPage):
            return deduplicate_unhashable(collection)
        return collection.with_items(deduplicate_unhashable(collection))  # pyright: ignore[reportArgumentType, reportReturnType]

    @classmethod
    def _create_unix_timestamp_iterator(
        cls,
        method: PaginationMethodT,
        /,
        *args: Any,
        timestamp: int | None,
        **kwargs: Any,
    ) -> Self:
        return cls(
            method,
            *args,
            **(kwargs | ({} if timestamp is None else {"to": timestamp + 1})),
        )


del _ITERATOR_SLOTS


class _BaseSyncPageIterator(
    BasePageIterator[SyncResourceMethodProtocol[_PageT], _PageT],
    Iterator[_PageT],
):
    __slots__ = ()

    _STOP_ITERATION_EXC = StopIteration

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


class _BaseAsyncPageIterator(
    BasePageIterator[AsyncResourceMethodProtocol[_PageT], _PageT],
    AsyncIterator[_PageT],
):
    __slots__ = ()

    _STOP_ITERATION_EXC = StopAsyncIteration

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


@final
class SyncPageIterator(_BaseSyncPageIterator[_PageT]):
    __slots__ = ()

    @overload
    def collect(
        self: SyncPageIterator[RawAPIPageResponse],
        *,
        deduplicate: bool = ...,
    ) -> list[RawAPIItem]: ...

    @overload
    def collect(
        self: SyncPageIterator[ItemPage[_T]],
        *,
        deduplicate: bool = ...,
    ) -> ItemPage[_T]: ...

    def collect(
        self: SyncPageIterator[RawAPIPageResponse] | SyncPageIterator[ItemPage[_T]],
        *,
        deduplicate: bool = True,
    ) -> ProcessedPages[_T]:
        return self.__class__.gather_from_iterator(self, deduplicate=deduplicate)

    @classmethod
    def unix(
        cls,
        method: SyncResourceMethodProtocol[_PageT],
        /,
        *args: Any,
        cfg: TimestampPaginationConfig,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        **kwargs: Any,
    ) -> Iterator[_PageT]:
        cls._validate_unix_pagination_parameter(cfg, method, kwargs)
        kwargs["max_items"] = max_items

        current_timestamp = None
        total_yielded = 0

        while True:
            iterator = cls._create_unix_timestamp_iterator(
                method, *args, timestamp=current_timestamp, **kwargs
            )

            last_page = None
            for page in iterator:
                yield page
                last_page = page
                total_yielded += iterator._effective_limit
                if total_yielded >= iterator.max_items:
                    return

            if last_page is None:
                break

            new_timestamp = cls._extract_unix_timestamp(cfg, last_page)
            if new_timestamp is None or new_timestamp == current_timestamp:
                break
            current_timestamp = new_timestamp

            kwargs["max_items"] = iterator.max_items - total_yielded

    @overload
    @classmethod
    def gather_from_iterator(
        cls,
        iterator: Iterator[RawAPIPageResponse],
        /,
        return_format: CollectReturnFormat = ...,
        *,
        deduplicate: bool = ...,
    ) -> list[RawAPIItem]: ...

    @overload
    @classmethod
    def gather_from_iterator(
        cls,
        iterator: Iterator[ItemPage[_T]],
        /,
        return_format: CollectReturnFormat = ...,
        *,
        deduplicate: bool = ...,
    ) -> ItemPage[_T]: ...

    @classmethod
    def gather_from_iterator(
        cls,
        iterator: Iterator[RawAPIPageResponse] | Iterator[ItemPage[_T]],
        /,
        return_format: CollectReturnFormat = CollectReturnFormat.FIRST,
        *,
        deduplicate: bool = True,
    ) -> ProcessedPages[_T]:
        return cls._process_collected_pages(list(iterator), return_format, deduplicate)


@final
class AsyncPageIterator(_BaseAsyncPageIterator[_PageT]):
    __slots__ = ()

    @overload
    async def collect(
        self: AsyncPageIterator[RawAPIPageResponse],
    ) -> list[RawAPIItem]: ...

    @overload
    async def collect(
        self: AsyncPageIterator[ItemPage[_T]],
    ) -> ItemPage[_T]: ...

    async def collect(
        self: AsyncPageIterator[RawAPIPageResponse] | AsyncPageIterator[ItemPage[_T]],
    ) -> ProcessedPages[_T]:
        return await self.__class__.gather_from_iterator(self)

    @classmethod
    async def unix(
        cls,
        method: AsyncResourceMethodProtocol[_PageT],
        /,
        *args: Any,
        cfg: TimestampPaginationConfig,
        max_items: MaxItemsType = BasePageIterator.DEFAULT_MAX_ITEMS,
        **kwargs: Any,
    ) -> AsyncIterator[_PageT]:
        cls._validate_unix_pagination_parameter(cfg, method, kwargs)
        kwargs["max_items"] = max_items

        current_timestamp = None
        total_yielded = 0

        while True:
            iterator = cls._create_unix_timestamp_iterator(
                method, *args, timestamp=current_timestamp, **kwargs
            )

            last_page = None
            async for page in iterator:
                yield page
                last_page = page
                total_yielded += iterator._effective_limit
                if total_yielded >= iterator.max_items:
                    return

            if last_page is None:
                break

            new_timestamp = cls._extract_unix_timestamp(cfg, last_page)
            if new_timestamp is None or new_timestamp == current_timestamp:
                break
            current_timestamp = new_timestamp

            kwargs["max_items"] = iterator.max_items - total_yielded

    @overload
    @classmethod
    async def gather_from_iterator(
        cls,
        iterator: AsyncIterator[RawAPIPageResponse],
        /,
        return_format: CollectReturnFormat = ...,
        *,
        deduplicate: bool = ...,
    ) -> list[RawAPIItem]: ...

    @overload
    @classmethod
    async def gather_from_iterator(
        cls,
        iterator: AsyncIterator[ItemPage[_T]],
        /,
        return_format: CollectReturnFormat = ...,
        *,
        deduplicate: bool = ...,
    ) -> ItemPage[_T]: ...

    @classmethod
    async def gather_from_iterator(
        cls,
        iterator: AsyncIterator[RawAPIPageResponse] | AsyncIterator[ItemPage[_T]],
        /,
        return_format: CollectReturnFormat = CollectReturnFormat.FIRST,
        *,
        deduplicate: bool = True,
    ) -> ProcessedPages[_T]:
        return cls._process_collected_pages(
            [page async for page in iterator], return_format, deduplicate
        )
