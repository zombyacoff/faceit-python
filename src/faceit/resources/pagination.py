from __future__ import annotations

import typing as t
import warnings
from abc import ABC
from inspect import Parameter, signature

from annotated_types import Le
from pydantic import Field
from pydantic.fields import FieldInfo

from faceit._types import RawAPIItem, RawAPIPageResponse, Self, TypeAlias
from faceit._utils import deep_get, get_hashable_representation, lazy_import
from faceit.constants import RAW_RESPONSE_ITEMS_KEY
from faceit.models import ItemPage, PaginationTimeRange

if t.TYPE_CHECKING:
    from .base import BaseResource


@lazy_import
def _get_base_resource_class() -> t.Type[BaseResource]:
    from .base import BaseResource  # noqa: PLC0415

    return BaseResource


_Func: TypeAlias = t.Callable[..., t.Any]

_T = t.TypeVar("_T")
_T_co = t.TypeVar("_T_co", covariant=True)

_PageType: TypeAlias = t.Union[ItemPage, RawAPIPageResponse]
_PageListType: TypeAlias = t.List[_PageType]
_PageT_co = t.TypeVar("_PageT_co", bound=_PageType, covariant=True)


class _BaseMethodProtocol(t.Protocol):
    __name__: str
    __call__: _Func


class BasePaginationMethod(_BaseMethodProtocol, t.Protocol[_T_co]):
    def __call__(
        self,
        *args: t.Any,
        offset: int = Field(...),
        limit: int = Field(...),
        **kwargs: t.Any,
    ) -> _T_co: ...


class SyncPaginationMethod(BasePaginationMethod[_PageT_co], t.Protocol): ...


class AsyncPaginationMethod(
    BasePaginationMethod[t.Awaitable[_PageT_co]], t.Protocol
): ...


class BaseUnixPaginationMethod(_BaseMethodProtocol, t.Protocol[_T_co]):
    def __call__(
        self,
        *args: t.Any,
        offset: int = Field(...),
        limit: int = Field(...),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
        **kwargs: t.Any,
    ) -> _T_co: ...


class SyncUnixPaginationMethod(
    BaseUnixPaginationMethod[_PageT_co], t.Protocol
): ...


class AsyncUnixPaginationMethod(
    BaseUnixPaginationMethod[t.Awaitable[_PageT_co]], t.Protocol
): ...


_MethodT = t.TypeVar("_MethodT", bound=_BaseMethodProtocol)


class UnixPaginationConfig(t.TypedDict):
    key: str
    attr: str


_UnixMethodRequiredKeys: t.Final[t.FrozenSet[str]] = frozenset(
    UnixPaginationConfig.__annotations__.keys()
)

_UnixPaginationConfigType: TypeAlias = t.Union[
    UnixPaginationConfig, t.Literal[False]
]


@t.final
class PaginationMaxParams(t.NamedTuple):
    limit: int
    offset: int


_PAGINATION_ARGS = PaginationMaxParams._fields
_UNIX_PAGINATION_PARAMS = PaginationTimeRange._fields

_CollectReturnFormat: TypeAlias = t.Literal["first", "raw", "model"]
_COLLECT_RETURN_FORMATS: t.Final[
    t.Dict[
        _CollectReturnFormat,
        t.Callable[
            [_PageListType],
            t.Union[t.Type[ItemPage], t.Type[RawAPIPageResponse]],
        ],
    ]
] = {
    "first": lambda collection: type(collection[0])
    if collection
    else RawAPIPageResponse,
    "raw": lambda _: RawAPIPageResponse,
    "model": lambda _: ItemPage,
}


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
            f"Function {method_name} is missing default value for limit or offset parameter"
        )
    if not isinstance(limit_param.default, FieldInfo) or not isinstance(
        offset_param.default, FieldInfo
    ):
        raise TypeError(
            f"Default value for limit or offset parameter in {method_name} is not a FieldInfo"
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
        # If offset constraint is missing,
        # use `max_limit` as the default `max_offset`
        max_limit
        if offset_constraint is None
        else t.cast(int, offset_constraint.le)
    )
    return PaginationMaxParams(max_limit, max_offset)


def check_pagination_support(
    func: _Func, /
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


class _MethodCall(t.NamedTuple, t.Generic[_MethodT]):
    call: _MethodT
    args: t.Tuple[t.Any, ...]
    kwargs: t.Dict[str, t.Any]


class BasePageIterator(t.Generic[_MethodT, _PageT_co], ABC):
    _STOP_ITERATION: t.ClassVar[t.Type[Exception]]

    UNIX_CFG: t.ClassVar = UnixPaginationConfig

    def __init__(
        self, method: _MethodT, /, *args: t.Any, **kwargs: t.Any
    ) -> None:
        pagination_limits = check_pagination_support(method)
        if pagination_limits is False:
            raise ValueError(
                f"Method '{method.__name__}' does not support pagination. "
                f"Ensure it's a BaseResource method with offset and limit parameters."
            )

        self._method = _MethodCall[_MethodT](
            call=method,
            args=args,
            kwargs=self.__class__._remove_pagination_args(**kwargs),
        )
        self._pagination_limits = pagination_limits
        self._init_iteration()

    def _init_iteration(self) -> None:
        self._exhausted = False
        self._offset = 0
        self._page_index = 0

    @property
    def exhausted(self) -> bool:
        return self._exhausted

    @property
    def current_offset(self) -> int:
        return self._offset

    @current_offset.setter
    def current_offset(self, value: t.Any, /) -> None:
        if not isinstance(value, int):
            raise TypeError(f"Pagination offset must be an integer: {value}")
        if self._exhausted:
            raise ValueError(
                "Pagination offset cannot be set after the iterator has been exhausted"
            )
        if value < 0:
            raise ValueError(f"Pagination offset cannot be negative: {value}")
        if value > self._pagination_limits.limit:
            raise ValueError(
                f"Pagination offset cannot exceed the maximum limit "
                f"({self._pagination_limits.limit}): {value}"
            )
        self._offset = value

    @property
    def current_page_index(self) -> int:
        return self._page_index

    def reset(self) -> None:
        self._init_iteration()

    def with_updated_args(self, *args: t.Any, **kwargs: t.Any) -> Self:
        return self.__class__(self._method.call, *args, **kwargs)

    @staticmethod
    def _remove_pagination_args(**kwargs: t.Any) -> t.Dict[str, t.Any]:
        if any(kwargs.pop(arg, None) for arg in _PAGINATION_ARGS):
            warnings.warn(
                f"Pagination parameters {_PAGINATION_ARGS} should not be provided by users. "
                f"These parameters are managed internally by the pagination system. ",
                UserWarning,
                stacklevel=2,
            )
        return kwargs

    def _handle_iteration_state(
        self, page: t.Optional[_PageT_co], /
    ) -> _PageT_co:
        if page is None:
            self._exhausted = True
            raise self.__class__._STOP_ITERATION

        self._page_index += 1
        self._offset += self._pagination_limits.limit

        is_page_smaller_than_limit = len(page) < self._pagination_limits.limit
        is_offset_exceeded = self._offset >= self._pagination_limits.offset
        self._exhausted = is_page_smaller_than_limit or is_offset_exceeded

        return page

    @staticmethod
    def _validate_unix_pagination_parameter(
        method: _MethodT,
        /,
        # Process `kwargs` to filter pagination parameters and issue warnings
        # when user-provided values will be ignored
        kwargs: t.Dict[str, t.Any],
        key: str,
        attr: str,
    ) -> None:
        if not _has_unix_pagination_params(method):
            raise ValueError(
                f"Method {method.__name__} does not appear to support Unix timestamp pagination. "
                f"Expected start and to parameters."
            )
        if any(
            not isinstance(value, str) or not value for value in (key, attr)
        ):
            raise ValueError(
                f"Key and attribute parameters must be non-empty strings: {key}, {attr}"
            )
        if any(kwargs.pop(arg, None) for arg in _UNIX_PAGINATION_PARAMS):
            warnings.warn(
                "The parameters start and to will be managed automatically "
                "with Unix timestamp pagination. Your provided values will be ignored.",
                UserWarning,
                stacklevel=3,
            )

    @staticmethod
    def _validate_unix_config(
        unix_config: _UnixPaginationConfigType, /
    ) -> None:
        if unix_config is not False and not isinstance(unix_config, dict):
            raise ValueError(
                f"Invalid unix pagination configuration: "
                f"expected UnixPaginationConfig dictionary or False, got {type(unix_config)}. "
                f"See pagination.UnixPaginationConfig for the required format."
            )
        if (
            isinstance(unix_config, dict)
            and _UnixMethodRequiredKeys - unix_config.keys()
        ):
            raise ValueError(
                f"Invalid unix pagination configuration: "
                f"missing required keys {_UnixMethodRequiredKeys}. "
                f"See pagination.UnixPaginationConfig for the required format."
            )

    @staticmethod
    def _extract_unix_timestamp(
        page: t.Optional[_PageT_co], key: str, attr: str, /
    ) -> t.Optional[int]:
        if not page:
            return None
        return (
            deep_get(page[RAW_RESPONSE_ITEMS_KEY][-1], key)
            if isinstance(page, dict)
            else getattr(page.last(), attr, None)
        )

    @classmethod
    def _process_collected_pages(
        cls,
        collection: t.List[_PageT_co],
        return_format: _CollectReturnFormat,
        deduplicate: bool,
        /,
    ) -> t.Union[ItemPage[_T], t.List[RawAPIItem]]:
        is_raw_mode = (
            _COLLECT_RETURN_FORMATS[return_format](
                t.cast(_PageListType, collection)
            )
            is RawAPIPageResponse
        )
        filtered = cls._filter_collection(
            collection, RawAPIPageResponse if is_raw_mode else ItemPage
        )
        processed = filtered if is_raw_mode else ItemPage.merge(filtered)
        return (
            cls._deduplicate_collection(processed)
            if deduplicate
            else processed
        )

    @staticmethod
    def _filter_collection(
        collection: t.List[_PageT_co], expected_type: t.Type[t.Any], /
    ) -> t.List[t.Any]:
        return [item for item in collection if isinstance(item, expected_type)]

    @classmethod
    def _deduplicate_collection(
        cls, collection: t.Union[ItemPage, t.List[RawAPIItem]], /
    ) -> t.Union[ItemPage, t.List[RawAPIItem]]:
        unique_items = list(
            {
                get_hashable_representation(item): item for item in collection
            }.values()
        )
        return (
            collection.with_items(unique_items)
            if isinstance(collection, ItemPage)
            else unique_items
        )

    @classmethod
    def _create_unix_timestamp_iterator(
        cls,
        method: _MethodT,
        /,
        *args: t.Any,
        timestamp: t.Optional[int],
        **kwargs: t.Any,
    ) -> Self:
        # fmt: off
        return cls(method, *args, **{
            **kwargs,
            **({"to": timestamp + 1} if timestamp is not None else {}),
        })
        # fmt: on


class SyncPageIterator(
    BasePageIterator[
        t.Union[
            SyncPaginationMethod[_PageT_co],
            SyncUnixPaginationMethod[_PageT_co],
        ],
        _PageT_co,
    ],
    t.Iterator[_PageT_co],
):
    _STOP_ITERATION: t.ClassVar = StopIteration

    def _fetch_page(self) -> t.Optional[_PageT_co]:
        return (
            self._method.call(
                *self._method.args,
                **self._method.kwargs,
                limit=self._pagination_limits.limit,
                offset=self._offset,
            )
            or None
        )

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> _PageT_co:
        if self._exhausted:
            raise self.__class__._STOP_ITERATION
        return self._handle_iteration_state(self._fetch_page())

    @classmethod
    def unix(
        cls,
        method: SyncUnixPaginationMethod[_PageT_co],
        /,
        *_args: t.Any,
        key: str,
        attr: str,
        **kwargs: t.Any,
    ) -> t.Generator[_PageT_co, None, None]:
        cls._validate_unix_pagination_parameter(method, kwargs, key, attr)

        current_timestamp = None
        while True:
            pages = list(
                cls._create_unix_timestamp_iterator(
                    method, *_args, timestamp=current_timestamp, **kwargs
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
    def collect(
        cls,
        method: SyncPaginationMethod[ItemPage[_T]],
        /,
        *args: t.Any,
        unix: t.Literal[False] = ...,
        return_format: _CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> ItemPage[_T]: ...

    @t.overload
    @classmethod
    def collect(
        cls,
        method: SyncPaginationMethod[RawAPIPageResponse],
        /,
        *args: t.Any,
        unix: t.Literal[False] = ...,
        return_format: _CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    @classmethod
    def collect(
        cls,
        method: SyncUnixPaginationMethod[ItemPage[_T]],
        /,
        *args: t.Any,
        unix: _UnixPaginationConfigType,
        return_format: _CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> ItemPage[_T]: ...

    @t.overload
    @classmethod
    def collect(
        cls,
        method: SyncUnixPaginationMethod[RawAPIPageResponse],
        /,
        *args: t.Any,
        unix: _UnixPaginationConfigType,
        return_format: _CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> t.List[RawAPIItem]: ...

    @classmethod
    def collect(
        cls,
        method: t.Union[
            SyncPaginationMethod[t.Union[ItemPage[_T], RawAPIPageResponse]],
            SyncUnixPaginationMethod[
                t.Union[ItemPage[_T], RawAPIPageResponse]
            ],
        ],
        /,
        *args: t.Any,
        unix: _UnixPaginationConfigType = False,
        return_format: _CollectReturnFormat = "first",
        deduplicate: bool = True,
        **kwargs: t.Any,
    ) -> t.Union[ItemPage[_T], t.List[RawAPIItem]]:
        cls._validate_unix_config(unix)
        if unix is False:
            casted_method = t.cast(
                t.Union[
                    SyncPaginationMethod[_PageT_co],
                    SyncUnixPaginationMethod[_PageT_co],
                ],
                method,
            )
            collection = list(cls(casted_method, *args, **kwargs))
        else:
            collection = list(
                cls.unix(
                    t.cast(SyncUnixPaginationMethod[_PageT_co], method),
                    *args,
                    **unix,
                    **kwargs,
                )
            )
        return cls._process_collected_pages(
            collection, return_format, deduplicate
        )


class AsyncPageIterator(
    BasePageIterator[
        t.Union[
            AsyncPaginationMethod[_PageT_co],
            AsyncUnixPaginationMethod[_PageT_co],
        ],
        _PageT_co,
    ],
    t.AsyncIterator[_PageT_co],
):
    _STOP_ITERATION: t.ClassVar = StopAsyncIteration

    async def _fetch_page(self) -> t.Optional[_PageT_co]:
        return (
            await self._method.call(
                *self._method.args,
                **self._method.kwargs,
                limit=self._pagination_limits.limit,
                offset=self._offset,
            )
            or None
        )

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> _PageT_co:
        if self._exhausted:
            raise self.__class__._STOP_ITERATION
        return self._handle_iteration_state(await self._fetch_page())

    @classmethod
    async def unix(
        cls,
        method: AsyncUnixPaginationMethod[_PageT_co],
        /,
        *_args: t.Any,
        key: str,
        attr: str,
        **kwargs: t.Any,
    ) -> t.AsyncGenerator[_PageT_co, None]:
        cls._validate_unix_pagination_parameter(method, kwargs, key, attr)

        current_timestamp = None
        while True:
            pages = [
                page
                async for page in cls._create_unix_timestamp_iterator(
                    method, *_args, timestamp=current_timestamp, **kwargs
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
    async def collect(
        cls,
        method: AsyncPaginationMethod[ItemPage[_T]],
        /,
        *args: t.Any,
        unix: t.Literal[False] = ...,
        return_format: _CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> ItemPage[_T]: ...

    @t.overload
    @classmethod
    async def collect(
        cls,
        method: AsyncPaginationMethod[RawAPIPageResponse],
        /,
        *args: t.Any,
        unix: t.Literal[False] = ...,
        return_format: _CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    @classmethod
    async def collect(
        cls,
        method: AsyncUnixPaginationMethod[ItemPage[_T]],
        /,
        *args: t.Any,
        unix: _UnixPaginationConfigType,
        return_format: _CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> ItemPage[_T]: ...

    @t.overload
    @classmethod
    async def collect(
        cls,
        method: AsyncUnixPaginationMethod[RawAPIPageResponse],
        /,
        *args: t.Any,
        unix: _UnixPaginationConfigType,
        return_format: _CollectReturnFormat = ...,
        deduplicate: bool = ...,
        **kwargs: t.Any,
    ) -> t.List[RawAPIItem]: ...

    @classmethod
    async def collect(
        cls,
        method: t.Union[
            AsyncPaginationMethod[t.Union[ItemPage[_T], RawAPIPageResponse]],
            AsyncUnixPaginationMethod[
                t.Union[ItemPage[_T], RawAPIPageResponse]
            ],
        ],
        /,
        *args: t.Any,
        unix: _UnixPaginationConfigType = False,
        return_format: _CollectReturnFormat = "first",
        deduplicate: bool = True,
        **kwargs: t.Any,
    ) -> t.Union[ItemPage[_T], t.List[RawAPIItem]]:
        cls._validate_unix_config(unix)
        if unix is False:
            casted_method = t.cast(
                t.Union[
                    AsyncPaginationMethod[_PageT_co],
                    AsyncUnixPaginationMethod[_PageT_co],
                ],
                method,
            )
            collection = [
                page async for page in cls(casted_method, *args, **kwargs)
            ]
        else:
            collection = [
                page
                async for page in cls.unix(
                    t.cast(AsyncUnixPaginationMethod[_PageT_co], method),
                    *args,
                    **unix,
                    **kwargs,
                )
            ]
        return cls._process_collected_pages(
            collection, return_format, deduplicate
        )
