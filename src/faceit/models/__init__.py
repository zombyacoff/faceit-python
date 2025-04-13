from __future__ import annotations

import typing as t
from itertools import chain, starmap
from random import choice

from pydantic import BaseModel, Field, field_validator

from faceit._types import Annotated, Self, TypeAlias
from faceit._utils import get_nested_property
from faceit.constants import RAW_RESPONSE_ITEMS_KEY

from .championship import Championship
from .match import Match
from .player import (
    BanEntry,
    BaseMatchPlayerStats,
    CS2MatchPlayerStats,
    GameInfo,
    GeneralTeam,
    Hub,
    Player,
    Tournament,
)

__all__ = (
    "BanEntry",
    "BaseMatchPlayerStats",
    "CS2MatchPlayerStats",
    "Championship",
    "GameInfo",
    "GeneralTeam",
    "Hub",
    "ItemPage",
    "Match",
    "Player",
    "Tournament",
)

_T = t.TypeVar("_T")

if t.TYPE_CHECKING:
    _R = t.TypeVar("_R")

_PAGINATION_UNSET: t.Final = -1

_PaginationLimit: TypeAlias = Annotated[int, Field(ge=_PAGINATION_UNSET)]


@t.final
class PaginationTimeRange(t.NamedTuple):
    start: _PaginationLimit
    to: _PaginationLimit


@t.final
class PaginationMetadata(t.NamedTuple):
    offset: _PaginationLimit
    limit: _PaginationLimit
    time_range: PaginationTimeRange


@t.final
class ItemPage(BaseModel, t.Generic[_T], frozen=True):
    items: Annotated[t.List[_T], Field(alias=RAW_RESPONSE_ITEMS_KEY)]

    _offset: Annotated[_PaginationLimit, Field(alias="start")]
    _limit: Annotated[_PaginationLimit, Field(alias="end")]

    __time_range_description: t.ClassVar = "Unix timestamp in milliseconds"
    _time_from: Annotated[
        _PaginationLimit,
        Field(
            _PAGINATION_UNSET,
            alias="from",
            description=__time_range_description,
        ),
    ]
    _time_to: Annotated[
        _PaginationLimit,
        Field(
            _PAGINATION_UNSET, alias="to", description=__time_range_description
        ),
    ]

    @property
    def metadata(self) -> PaginationMetadata:
        return PaginationMetadata(self._offset, self._limit, self.time_range)

    @property
    def time_range(self) -> PaginationTimeRange:
        return PaginationTimeRange(self._time_from, self._time_to)

    @property
    def page(self) -> int:
        return (self._offset // self._limit) + 1 if self._limit else 1

    @t.overload
    def find(self, attr: str, value: t.Any) -> t.Optional[_T]: ...

    @t.overload
    def find(
        self, attr: str, value: t.Any, default: _R
    ) -> t.Union[_T, _R]: ...

    def find(self, attr: str, value: t.Any, default: t.Any = None) -> t.Any:
        if not self.items:
            return default
        return next(
            (
                item
                for item in self.items
                if get_nested_property(item, attr) == value
            ),
            default,
        )

    def find_all(self, attr: str, value: t.Any) -> t.List[_T]:
        return [
            item
            for item in self.items
            if get_nested_property(item, attr) == value
        ]

    @t.overload
    def first(self) -> t.Optional[_T]: ...

    @t.overload
    def first(self, default: _R, /) -> t.Union[_T, _R]: ...

    def first(self, default: t.Any = None) -> t.Any:
        return self.items[0] if self.items else default

    @t.overload
    def last(self) -> t.Optional[_T]: ...

    @t.overload
    def last(self, default: _R, /) -> t.Union[_T, _R]: ...

    def last(self, default: t.Any = None) -> t.Any:
        return self.items[-1] if self.items else default

    @t.overload
    def random(self) -> t.Optional[_T]: ...

    @t.overload
    def random(self, default: _R, /) -> t.Union[_T, _R]: ...

    def random(self, default: t.Any = None) -> t.Any:
        # Intentionally using non-cryptographic RNG as this is for
        # convenience sampling rather than security-sensitive operations
        return choice(self.items) if self.items else default  # noqa: S311

    def map(self, func: t.Callable[[_T], _R], /) -> ItemPage[_R]:
        return self.__class__._construct_without_pagination(
            list(map(func, self.items))
        )

    def filter(self, predicate: t.Callable[[_T], bool], /) -> Self:
        return self.__class__._construct_without_pagination(
            list(filter(predicate, self.items))
        )

    def with_items(self, new_items: t.List[_T], /) -> Self:
        return self.model_copy(update={"items": new_items})

    @classmethod
    # Using `ItemPage[_R]` return type and `type: ignore`
    # to support generic type transformation when called from
    # methods like `map()` that change the item type from `_T` to `_R`
    def _construct_without_pagination(
        cls, items: t.List[_R] | None = None, /
    ) -> ItemPage[_R]:
        return cls.model_construct(
            items=items or [],
            offset=_PAGINATION_UNSET,
            limit=_PAGINATION_UNSET,
        )  # type: ignore[return-value]

    @classmethod
    def merge(cls, pages: t.Iterable[ItemPage[_T]], /) -> ItemPage[_T]:
        return cls._construct_without_pagination(
            list(chain.from_iterable(pages))
        )

    def __bool__(self) -> bool:
        return bool(self.items)

    def __contains__(self, item: t.Any) -> bool:
        return item in self.items

    @t.overload
    def __getitem__(self, index: t.SupportsIndex) -> _T: ...

    @t.overload
    def __getitem__(self, index: slice) -> Self: ...

    def __getitem__(
        self, index: t.Union[t.SupportsIndex, slice]
    ) -> t.Union[_T, Self]:
        if isinstance(index, slice):
            return self.with_items(self.items[index])
        try:
            return self.items[index.__index__()]
        except IndexError as e:
            raise IndexError(f"ItemPage index out of range: {index}") from e
        except (TypeError, AttributeError) as e:
            raise TypeError(
                f"ItemPage indices must be objects supporting "
                f"__index__ or slices, not {type(index).__name__}"
            ) from e

    def __iter__(self) -> t.Iterator[_T]:  # type: ignore[override]
        yield from self.items

    def __len__(self) -> int:
        return len(self.items)

    def __reversed__(self) -> Self:
        return self.with_items(list(reversed(self.items)))

    def __str__(self) -> str:
        return str(self.items)

    @field_validator(RAW_RESPONSE_ITEMS_KEY, mode="before")
    def normalize_items(cls, items: t.Any) -> t.List[t.Dict[str, t.Any]]:  # noqa: N805
        if not isinstance(items, list):
            raise TypeError(
                f"Expected {RAW_RESPONSE_ITEMS_KEY} to be a list, got {type(items).__name__}"
            )

        def normalize_item(i: int, item: t.Any) -> t.Dict[str, t.Any]:
            if not isinstance(item, dict):
                raise TypeError(
                    f"Element at index {i} must be a dictionary, got {type(item).__name__}"
                )

            if len(item) == 1:  # Flatten single-item dictionaries
                _, value = next(iter(item.items()))
                if isinstance(value, dict):
                    return value

            return item

        return list(starmap(normalize_item, enumerate(items)))
