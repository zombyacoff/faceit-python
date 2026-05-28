from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from itertools import chain, starmap
from random import choice as random_choice
from typing import Annotated, Any, Generic, SupportsIndex, final, overload

from pydantic import (
    BaseModel,
    Field,
    NonNegativeInt,
    PositiveInt,
    computed_field,
    field_validator,
)

from faceit.constants import RAW_RESPONSE_ITEMS_KEY
from faceit.models.custom_types import TimestampMs
from faceit.types import _T, _TT
from faceit.utils import get_nested_property


@final
class PaginationTimeRange(BaseModel, frozen=True):
    start: TimestampMs
    to: TimestampMs


@final
class PaginationMetadata(BaseModel, frozen=True):
    offset: NonNegativeInt
    limit: PositiveInt
    time_range: PaginationTimeRange | None


@final
class ItemPage(
    BaseModel,
    Generic[_T],
    frozen=True,
    populate_by_name=True,
):
    items: tuple[_T, ...]

    offset: Annotated[
        NonNegativeInt | None,
        Field(None, alias="start", exclude=True),
    ]
    limit: Annotated[
        PositiveInt | None,
        Field(None, alias="end", exclude=True),
    ]

    time_from: Annotated[
        TimestampMs | None,
        Field(None, alias="from", exclude=True),
    ]
    """Unix time in milliseconds to start the range."""
    time_to: Annotated[
        TimestampMs | None,
        Field(None, alias="to", exclude=True),
    ]
    """Unix time in milliseconds to end the range."""

    @property
    def time_range(self) -> PaginationTimeRange | None:
        if self.time_from is None or self.time_to is None:
            return None
        return PaginationTimeRange(start=self.time_from, to=self.time_to)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def metadata(self) -> PaginationMetadata | None:
        if self.offset is None or self.limit is None:
            return None
        return PaginationMetadata(
            offset=self.offset, limit=self.limit, time_range=self.time_range
        )

    @overload
    def find(self, attr: str, value: object) -> _T | None: ...

    @overload
    def find(self, attr: str, value: object, default: _TT) -> _T | _TT: ...

    def find(
        self, attr: str, value: object, default: _TT | None = None
    ) -> _T | _TT | None:
        return next(self._find_items(attr, value), default)

    def find_all(self, attr: str, value: object) -> ItemPage[_T]:
        return self.__class__._construct_without_metadata(self._find_items(attr, value))

    @overload
    def get_first(self) -> _T | None: ...

    @overload
    def get_first(self, default: _TT, /) -> _T | _TT: ...

    def get_first(self, default: _TT | None = None) -> _T | _TT | None:
        return self[0] if self else default

    @overload
    def get_last(self) -> _T | None: ...

    @overload
    def get_last(self, default: _TT, /) -> _T | _TT: ...

    def get_last(self, default: _TT | None = None) -> _T | _TT | None:
        return self[-1] if self else default

    @overload
    def get_random(self) -> _T | None: ...

    @overload
    def get_random(self, default: _TT, /) -> _T | _TT: ...

    def get_random(self, default: _TT | None = None) -> _T | _TT | None:
        # Intentionally using non-cryptographic RNG as this is for
        # convenience sampling rather than security-sensitive operations
        return random_choice(self) if self else default  # noqa: S311

    def map(self, func: Callable[[_T], _TT], /) -> ItemPage[_TT]:
        return self.__class__._construct_without_metadata(map(func, self))

    def filter(self, predicate: Callable[[_T], bool], /) -> ItemPage[_T]:
        return self.__class__._construct_without_metadata(filter(predicate, self))

    def _find_items(self, attr: str, value: object, /) -> Iterator[_T]:
        return (item for item in self if get_nested_property(item, attr) == value)

    @classmethod
    def merge(cls, pages: Iterable[ItemPage[_TT]], /) -> ItemPage[_TT]:
        return cls._construct_without_metadata(chain.from_iterable(pages))

    @classmethod
    def with_items(cls, new_items: Iterable[_T], /) -> ItemPage[_T]:
        return cls._construct_without_metadata(new_items)

    @classmethod
    def _construct_without_metadata(
        cls, items: Iterable[_TT] | None = None, /
    ) -> ItemPage[_TT]:
        # fmt: off
        return cls.model_construct(  # type: ignore[return-value]
            items=tuple(items or ()),
            offset=None, limit=None,
            time_from=None, time_to=None,
        )
        # fmt: on

    def __iter__(self) -> Iterator[_T]:  # type: ignore[override]
        yield from self.items

    def __len__(self) -> int:
        return len(self.items)

    def __reversed__(self) -> ItemPage[_T]:
        return self.__class__._construct_without_metadata(reversed(self.items))

    @overload
    def __getitem__(self, index: SupportsIndex) -> _T: ...

    @overload
    def __getitem__(self, index: slice) -> ItemPage[_T]: ...

    def __getitem__(self, index: SupportsIndex | slice) -> _T | ItemPage[_T]:
        if isinstance(index, slice):
            return self.__class__._construct_without_metadata(self.items[index])
        try:
            return self.items[index.__index__()]
        except IndexError as e:
            msg = f"ItemPage index out of range: {index}"
            raise IndexError(msg) from e
        except (TypeError, AttributeError) as e:
            msg = (
                "ItemPage indices must be objects supporting "
                f"__index__ or slices, not {type(index).__name__}"
            )
            raise TypeError(msg) from e

    def __contains__(self, item: object) -> bool:
        return item in self.items

    def __bool__(self) -> bool:
        return bool(self.items)

    @field_validator(RAW_RESPONSE_ITEMS_KEY, mode="before")
    @classmethod
    def _normalize_items(cls, items: Any) -> tuple[dict[str, Any], ...]:
        if not isinstance(items, Iterable):
            msg = f"Expected {RAW_RESPONSE_ITEMS_KEY} to be an iterable, got {type(items).__name__}"
            raise ValueError(msg)  # noqa: TRY004

        def normalize_item(i: int, item: Any) -> dict[str, Any]:
            if not isinstance(item, dict):
                msg = f"Element at index {i} must be a dictionary, got {type(item).__name__}"
                raise ValueError(msg)  # noqa: TRY004

            if len(item) == 1:
                value = next(iter(item.values()))
                if isinstance(value, dict):
                    return value

            return item

        return tuple(starmap(normalize_item, enumerate(items)))
