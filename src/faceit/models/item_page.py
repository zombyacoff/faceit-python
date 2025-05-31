from __future__ import annotations

import typing
from functools import cached_property
from itertools import chain, starmap
from random import choice

from pydantic import BaseModel, Field, field_validator
from typing_extensions import Annotated, Self, TypeAlias

from faceit.constants import RAW_RESPONSE_ITEMS_KEY
from faceit.types import _R, _T
from faceit.utils import UnsetValue, get_nested_property

_PaginationLimit: TypeAlias = Annotated[
    int, Field(ge=UnsetValue.UNSET)  # [-1: unlimited)
]


@typing.final
class PaginationTimeRange(typing.NamedTuple):
    start: _PaginationLimit
    to: _PaginationLimit


@typing.final
class PaginationMetadata(typing.NamedTuple):
    offset: _PaginationLimit
    limit: _PaginationLimit
    time_range: PaginationTimeRange


@typing.final
class ItemPage(BaseModel, typing.Generic[_T], frozen=True):
    items: Annotated[typing.Tuple[_T, ...], Field(alias=RAW_RESPONSE_ITEMS_KEY)]

    _offset: Annotated[_PaginationLimit, Field(alias="start")]
    _limit: Annotated[_PaginationLimit, Field(alias="end")]

    _time_from: Annotated[
        _PaginationLimit,
        # 1746316800000 = UTC timestamp for 2025-05-04 00:00:00, in milliseconds
        Field(UnsetValue.UNSET, alias="from", examples=[1746316800000]),
    ]
    """Unix time in milliseconds to start the range."""
    _time_to: Annotated[
        _PaginationLimit,
        Field(UnsetValue.UNSET, alias="to", examples=[1746316800000]),
    ]
    """Unix time in milliseconds to end the range."""

    # NOTE: These properties use cached_property since the model is frozen and
    # underlying attributes (`_offset`, `_limit`, etc.) cannot change,
    # making repeated calculations unnecessary

    @cached_property
    def metadata(self) -> PaginationMetadata:
        return PaginationMetadata(self._offset, self._limit, self.time_range)

    @cached_property
    def time_range(self) -> PaginationTimeRange:
        return PaginationTimeRange(self._time_from, self._time_to)

    @cached_property
    def page(self) -> int:
        return (self._offset // self._limit) + 1 if self._limit else 1

    @typing.overload
    def find(self, attr: str, value: typing.Any) -> typing.Optional[_T]: ...

    @typing.overload
    def find(
        self, attr: str, value: typing.Any, default: _R
    ) -> typing.Union[_T, _R]: ...

    def find(
        self, attr: str, value: typing.Any, default: typing.Optional[_R] = None
    ) -> typing.Union[_T, _R, None]:
        return next(self._find_items(attr, value), default)

    def find_all(self, attr: str, value: typing.Any) -> typing.List[_T]:
        return list(self._find_items(attr, value))

    @typing.overload
    def first(self) -> typing.Optional[_T]: ...

    @typing.overload
    def first(self, default: _R, /) -> typing.Union[_T, _R]: ...

    def first(self, default: typing.Optional[_R] = None) -> typing.Union[_T, _R, None]:
        return self[0] if self else default

    @typing.overload
    def last(self) -> typing.Optional[_T]: ...

    @typing.overload
    def last(self, default: _R, /) -> typing.Union[_T, _R]: ...

    def last(self, default: typing.Optional[_R] = None) -> typing.Union[_T, _R, None]:
        return self[-1] if self else default

    @typing.overload
    def random(self) -> typing.Optional[_T]: ...

    @typing.overload
    def random(self, default: _R, /) -> typing.Union[_T, _R]: ...

    def random(self, default: typing.Optional[_R] = None) -> typing.Union[_T, _R, None]:
        # Intentionally using non-cryptographic RNG as this is for
        # convenience sampling rather than security-sensitive operations
        return choice(self) if self else default  # noqa: S311

    def map(self, func: typing.Callable[[_T], _R], /) -> ItemPage[_R]:
        return self.__class__._construct_without_metadata(map(func, self))

    def filter(self, predicate: typing.Callable[[_T], bool], /) -> Self:
        return self.__class__._construct_without_metadata(filter(predicate, self))

    def with_items(self, new_items: typing.Iterable[_T], /) -> Self:
        return self.model_copy(update={"items": tuple(new_items)})

    def _find_items(self, attr: str, value: typing.Any, /) -> typing.Iterator[_T]:
        return (item for item in self if get_nested_property(item, attr) == value)

    @classmethod
    def merge(cls, pages: typing.Iterable[ItemPage[_T]], /) -> ItemPage[_T]:
        return cls._construct_without_metadata(chain.from_iterable(pages))

    # fmt: off
    @classmethod
    def _construct_without_metadata(
        cls, items: typing.Optional[typing.Iterable[_R]] = None, /,
        # Using `ItemPage[_R]` return type and `type: ignore`
        # to support generic type transformation when called from
        # methods like `map()` that change the item type from `_T` to `_R`
    ) -> ItemPage[_R]:
        return cls.model_construct(  # type: ignore[return-value]
            items=items or (),
            _offset=UnsetValue.UNSET, _limit=UnsetValue.UNSET,
            _time_from=UnsetValue.UNSET, _time_to=UnsetValue.UNSET,
        )
    # fmt: on

    def __iter__(self) -> typing.Iterator[_T]:  # type: ignore[override]
        yield from self.items

    def __len__(self) -> int:
        return len(self.items)

    def __reversed__(self) -> Self:
        return self.with_items(tuple(reversed(self)))

    def __reduce__(
        self,
    ) -> typing.Tuple[typing.Type[Self], typing.Tuple[typing.Any, ...]]:
        # fmt: off
        return (self.__class__, (
            self.items, self._offset, self._limit, self._time_from, self._time_to,
        ))
        # fmt: on

    @typing.overload
    def __getitem__(self, index: typing.SupportsIndex) -> _T: ...

    @typing.overload
    def __getitem__(self, index: slice) -> Self: ...

    def __getitem__(
        self, index: typing.Union[typing.SupportsIndex, slice]
    ) -> typing.Union[_T, Self]:
        if isinstance(index, slice):
            return self.with_items(self.items[index])
        try:
            return self.items[index.__index__()]
        except IndexError as e:
            raise IndexError(f"ItemPage index out of range: {index}") from e
        except (TypeError, AttributeError) as e:
            raise TypeError(
                "ItemPage indices must be objects supporting "
                f"__index__ or slices, not {type(index).__name__}"
            ) from e

    def __contains__(self, item: typing.Any) -> bool:
        return item in self.items

    def __bool__(self) -> bool:
        return bool(self.items)

    def __str__(self) -> str:
        return str(self.items)

    @field_validator(RAW_RESPONSE_ITEMS_KEY, mode="before")
    def _normalize_items(
        cls, items: typing.Any
    ) -> typing.Tuple[typing.Dict[str, typing.Any], ...]:
        if not isinstance(items, list):
            raise TypeError(
                f"Expected {RAW_RESPONSE_ITEMS_KEY} to be a list, got {type(items).__name__}"
            )

        def normalize_item(i: int, item: typing.Any) -> typing.Dict[str, typing.Any]:
            if not isinstance(item, dict):
                raise TypeError(
                    f"Element at index {i} must be a dictionary, got {type(item).__name__}"
                )

            if len(item) == 1:
                value = next(iter(item.values()))
                if isinstance(value, dict):
                    return value

            return item

        return tuple(starmap(normalize_item, enumerate(items)))
