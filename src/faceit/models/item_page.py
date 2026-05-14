from __future__ import annotations

import typing
from itertools import chain, starmap
from random import choice as random_choice

from pydantic import (
    BaseModel,
    Field,
    NonNegativeInt,
    PositiveInt,
    computed_field,
    field_validator,
)
from typing_extensions import Annotated, Self, deprecated

from faceit.constants import RAW_RESPONSE_ITEMS_KEY
from faceit.models.custom_types import TimestampMs  # noqa: TC001
from faceit.types import _R, _T
from faceit.utils import get_nested_property


@typing.final
class PaginationTimeRange(BaseModel, frozen=True):
    start: TimestampMs
    to: TimestampMs


@typing.final
class PaginationMetadata(BaseModel, frozen=True):
    offset: NonNegativeInt
    limit: PositiveInt
    time_range: typing.Optional[PaginationTimeRange]


# fmt: off
@typing.final
class ItemPage(BaseModel, typing.Generic[_T],
    frozen=True,
    populate_by_name=True,
):
    # fmt: on
    items: typing.Tuple[_T, ...]

    offset: Annotated[
        typing.Optional[NonNegativeInt],
        Field(None, alias="start", exclude=True),
    ]
    limit: Annotated[
        typing.Optional[PositiveInt],
        Field(None, alias="end", exclude=True),
    ]

    time_from: Annotated[
        typing.Optional[TimestampMs],
        Field(None, alias="from", exclude=True),
    ]
    """Unix time in milliseconds to start the range."""
    time_to: Annotated[
        typing.Optional[TimestampMs],
        Field(None, alias="to", exclude=True),
    ]
    """Unix time in milliseconds to end the range."""

    @property
    def time_range(self) -> typing.Optional[PaginationTimeRange]:
        if self.time_from is None or self.time_to is None:
            return None
        return PaginationTimeRange(start=self.time_from, to=self.time_to)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def metadata(self) -> typing.Optional[PaginationMetadata]:
        if self.offset is None or self.limit is None:
            return None
        return PaginationMetadata(
            offset=self.offset,
            limit=self.limit,
            time_range=self.time_range,
        )

    @computed_field(deprecated=True)  # type: ignore[prop-decorator]
    @property
    # This property is redundant because all metadata is reset during page merging
    # to avoid complex calculations that would likely be inaccurate anyway
    @deprecated("`page` is deprecated and will be removed in a future version.")
    def page(self) -> typing.Optional[int]:
        return None if self.offset is None or self.limit is None else 1

    @typing.overload
    def find(self, attr: str, value: object) -> typing.Optional[_T]: ...

    @typing.overload
    def find(self, attr: str, value: object, default: _R) -> typing.Union[_T, _R]: ...

    def find(
        self, attr: str, value: object, default: typing.Optional[_R] = None
    ) -> typing.Union[_T, _R, None]:
        return next(self._find_items(attr, value), default)

    def find_all(self, attr: str, value: object) -> ItemPage[_T]:
        return self.__class__._construct_without_metadata(self._find_items(attr, value))

    @typing.overload
    def get_first(self) -> typing.Optional[_T]: ...

    @typing.overload
    def get_first(self, default: _R, /) -> typing.Union[_T, _R]: ...

    def get_first(
        self, default: typing.Optional[_R] = None
    ) -> typing.Union[_T, _R, None]:
        return self[0] if self else default

    @typing.overload
    def get_last(self) -> typing.Optional[_T]: ...

    @typing.overload
    def get_last(self, default: _R, /) -> typing.Union[_T, _R]: ...

    def get_last(
        self, default: typing.Optional[_R] = None
    ) -> typing.Union[_T, _R, None]:
        return self[-1] if self else default

    @typing.overload
    def get_random(self) -> typing.Optional[_T]: ...

    @typing.overload
    def get_random(self, default: _R, /) -> typing.Union[_T, _R]: ...

    def get_random(
        self, default: typing.Optional[_R] = None
    ) -> typing.Union[_T, _R, None]:
        # Intentionally using non-cryptographic RNG as this is for
        # convenience sampling rather than security-sensitive operations
        return random_choice(self) if self else default  # noqa: S311

    def map(self, func: typing.Callable[[_T], _R], /) -> ItemPage[_R]:
        return self.__class__._construct_without_metadata(map(func, self))

    def filter(self, predicate: typing.Callable[[_T], bool], /) -> ItemPage[_T]:
        return self.__class__._construct_without_metadata(filter(predicate, self))

    def _find_items(self, attr: str, value: object, /) -> typing.Iterator[_T]:
        return (item for item in self if get_nested_property(item, attr) == value)

    @classmethod
    def merge(cls, pages: typing.Iterable[ItemPage[_R]], /) -> ItemPage[_R]:
        return cls._construct_without_metadata(chain.from_iterable(pages))

    @classmethod
    def with_items(cls, new_items: typing.Iterable[_T], /) -> ItemPage[_T]:
        return cls._construct_without_metadata(new_items)

    @classmethod
    def _construct_without_metadata(
        cls, items: typing.Optional[typing.Iterable[_R]] = None, /
    ) -> ItemPage[_R]:
        # fmt: off
        return cls.model_construct(  # type: ignore[return-value]
            items=tuple(items or ()),
            offset=None, limit=None,
            time_from=None, time_to=None,
        )
        # fmt: on

    def __iter__(self) -> typing.Iterator[_T]:  # type: ignore[override]
        yield from self.items

    def __len__(self) -> int:
        return len(self.items)

    def __reversed__(self) -> ItemPage[_T]:
        return self.__class__._construct_without_metadata(reversed(self.items))

    @typing.overload
    def __getitem__(self, index: typing.SupportsIndex) -> _T: ...

    @typing.overload
    def __getitem__(self, index: slice) -> Self: ...

    def __getitem__(
        self, index: typing.Union[typing.SupportsIndex, slice]
    ) -> typing.Union[_T, ItemPage[_T]]:
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
    def _normalize_items(
        cls, items: typing.Any
    ) -> typing.Tuple[typing.Dict[str, typing.Any], ...]:
        if not isinstance(items, typing.Iterable):
            msg = f"Expected {RAW_RESPONSE_ITEMS_KEY} to be an iterable, got {type(items).__name__}"
            raise ValueError(msg)  # noqa: TRY004

        def normalize_item(i: int, item: typing.Any) -> typing.Dict[str, typing.Any]:
            if not isinstance(item, dict):
                msg = f"Element at index {i} must be a dictionary, got {type(item).__name__}"
                raise ValueError(msg)  # noqa: TRY004

            if len(item) == 1:
                value = next(iter(item.values()))
                if isinstance(value, dict):
                    return value

            return item

        return tuple(starmap(normalize_item, enumerate(items)))
