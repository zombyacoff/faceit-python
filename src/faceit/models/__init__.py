from __future__ import annotations

from random import choice
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Final,
    Generic,
    Iterator,
    List,
    NamedTuple,
    Optional,
    SupportsIndex,
    Union,
    final,
    overload,
)

from pydantic import BaseModel, Field, field_validator

from faceit.constants import RAW_RESPONSE_ITEMS_KEY
from faceit.types import Annotated, Self, TypeAlias, TypeVar
from faceit.utils import get_nested_property

from .championship import Championship
from .match import Match
from .player import BanEntry, BaseMatchPlayerStats, CS2MatchPlayerStats, GameInfo, GeneralTeam, Hub, Player, Tournament

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

_T = TypeVar("_T")
_R = TypeVar("_R")

_PAGINATION_UNSET: Final = -1

_PaginationLimit: TypeAlias = Union[Annotated[int, Field(ge=_PAGINATION_UNSET)]]


@final
class PaginationTimeRange(NamedTuple):
    start: _PaginationLimit
    to: _PaginationLimit


@final
class PaginationMetadata(NamedTuple):
    offset: _PaginationLimit
    limit: _PaginationLimit
    time_range: PaginationTimeRange


@final
class ItemPage(BaseModel, Generic[_T], frozen=True):
    """A paginated collection of items from the FACEIT API with metadata.

    This class represents a page of items from a paginated API response, providing
    rich functionality for accessing, filtering, and transforming the contained items
    while preserving pagination metadata.

    It implements a collection-like interface that allows direct access to items via
    indexing, iteration, and other common sequence operations. Additionally, it provides
    helper methods for finding, filtering, and transforming items.

    ItemPage is designed to work with the FACEIT API pagination pattern and handles
    normalization of inconsistent response formats through its validator.

    Attributes:
        items: List of items in the current page.
        offset: Starting index of this page (0-based).
        limit: Maximum number of items in the page.
        time_from: Optional starting timestamp for time-constrained queries (milliseconds).
        time_to: Optional ending timestamp for time-constrained queries (milliseconds).

    Examples:
        Accessing items:
        ```
        # Get first item
        first_item = page[0]

        # Iterate through items
        for item in page: ...

        # Check if page contains an item
        if specific_item in page: ...
        ```

        Filtering and transformation:
        ```
        # Filter items by a predicate
        filtered_items = page.filter(lambda item: item.game_id == "GameID.CS2")

        # Transform items
        usernames = page.map(lambda item: item.nickname)

        # Find items by attribute
        player = page.find("nickname", "player123")
        ```

        Combining pages:
        ```
        # Concatenate two pages
        combined_page = page1 + page2
        ```
    """

    _time_range_description: ClassVar = "Unix timestamp in milliseconds"

    items: Annotated[List[_T], Field(alias=RAW_RESPONSE_ITEMS_KEY)]

    offset: Annotated[_PaginationLimit, Field(alias="start")]
    limit: Annotated[_PaginationLimit, Field(alias="end")]
    # fmt: off
    time_from: Annotated[
        _PaginationLimit, Field(
            _PAGINATION_UNSET, alias="from", description=_time_range_description
        )
    ]
    time_to: Annotated[
        _PaginationLimit, Field(
            _PAGINATION_UNSET, alias="to", description=_time_range_description
        )
    ]
    # fmt: on

    @property
    def page(self) -> int:
        return (self.offset // self.limit) + 1 if self.limit else 1

    @property
    def time_range(self) -> PaginationTimeRange:
        return PaginationTimeRange(self.time_from, self.time_to)

    @property
    def metadata(self) -> PaginationMetadata:
        return PaginationMetadata(self.offset, self.limit, self.time_range)

    def preserve_metadata_with_items(self, new_items: List[_T], /) -> Self:
        """Create a new instance with provided items while preserving pagination metadata.

        This method allows replacing the collection's items while maintaining the original
        pagination context `(offset, limit, time range)`.

        Args:
            new_items: The new collection of items to use

        Returns:
            A new instance with the provided items and preserved metadata
        """
        return self.model_copy(update={"items": new_items})

    def map(self, func: Callable[[_T], _R], /) -> ItemPage[_R]:
        """Apply a function to each item in the collection and return a new collection.

        This method transforms items but does not preserve pagination metadata.
        The returned `ItemPage` may contain items of a different type than the original
        collection, depending on what the mapping function returns.

        Args:
            func: Function to apply to each item, can return any type

        Returns:
            A new `ItemPage` containing the transformed items with reset pagination metadata
        """
        mapped_items = [func(item) for item in self.items]
        # Type checker reports an error because we're returning `ItemPage[_R]` while the method
        # is defined on `ItemPage[_T]`. This is intentional as we're transforming item types
        # from `_T` to `_R`. The Generic parameter changes with the mapping operation
        return self.__class__.model_construct(items=mapped_items, offset=_PAGINATION_UNSET, limit=_PAGINATION_UNSET)  # type: ignore[return-value]

    def filter(self, predicate: Callable[[_T], bool], /) -> Self:
        """Filter items in the collection based on a predicate function.

        This method filters items but does not preserve pagination metadata.
        The returned `ItemPage` will have reset pagination metadata.

        Args:
            predicate: Function that returns `True` for items to keep

        Returns:
            A new collection containing only items for which the predicate returns True
        """
        filtered_items = [item for item in self.items if predicate(item)]
        return self.__class__.model_construct(items=filtered_items, offset=_PAGINATION_UNSET, limit=_PAGINATION_UNSET)

    @overload
    def first(self) -> Optional[_T]: ...
    @overload
    def first(self, default: _R, /) -> Union[_T, _R]: ...
    def first(self, default: Any = None) -> Any:
        """Return the first item in the collection or a default value if empty.

        Args:
            default: Value to return if the collection is empty

        Returns:
            The first item in the collection, or the default value if empty
        """
        return self.items[0] if self.items else default

    @overload
    def last(self) -> Optional[_T]: ...
    @overload
    def last(self, default: _R, /) -> Union[_T, _R]: ...
    def last(self, default: Any = None) -> Any:
        """Return the last item in the collection or a default value if empty.

        Args:
            default: Value to return if the collection is empty

        Returns:
            The last item in the collection, or the default value if empty
        """
        return self.items[-1] if self.items else default

    @overload
    def random(self) -> Optional[_T]: ...
    @overload
    def random(self, default: _R, /) -> Union[_T, _R]: ...
    def random(self, default: Any = None) -> Any:
        """Return a random item from the collection or a default value if empty.

        Args:
            default: Value to return if the collection is empty

        Returns:
            A randomly selected item from the collection, or the default value if empty
        """
        return choice(self.items) if self.items else default

    @overload
    def find(self, attr: str, value: Any) -> Optional[_T]: ...
    @overload
    def find(self, attr: str, value: Any, default: _R) -> Union[_T, _R]: ...
    def find(self, attr: str, value: Any, default: Any = None) -> Any:
        """Find the first item with a matching attribute value.

        Uses dot notation to access nested attributes (e.g., "player.nickname").

        Args:
            attr: Attribute name or path in dot notation
            value: Value to match against
            default: Value to return if no matching item is found

        Returns:
            The first matching item, or the default value if none found
        """
        if not self.items:
            return default
        return next((item for item in self.items if get_nested_property(item, attr) == value), default)

    def find_all(self, attr: str, value: Any) -> List[_T]:
        """Find all items with a matching attribute value.

        Uses dot notation to access nested attributes (e.g., "player.nickname").

        Args:
            attr: Attribute name or path in dot notation
            value: Value to match against

        Returns:
            List of all items with matching attribute value
        """
        return [item for item in self.items if get_nested_property(item, attr) == value]

    def __str__(self) -> str:
        return str(self.items)

    def __bool__(self) -> bool:
        return bool(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __contains__(self, item: Any) -> bool:
        return item in self.items

    # Suppressing type checking warning because we're overriding `BaseModel.__iter__`
    # which returns `Generator[Tuple[str, Any], None, None]`.
    # Using `Iterator[_T]` simplifies typing while providing the expected behavior.
    def __iter__(self) -> Iterator[_T]:  # type: ignore[override]
        yield from self.items

    @overload
    def __getitem__(self, index: SupportsIndex) -> _T: ...
    @overload
    def __getitem__(self, index: slice) -> Self: ...
    def __getitem__(self, index: Union[SupportsIndex, slice]) -> Union[_T, Self]:
        if isinstance(index, slice):
            return self.preserve_metadata_with_items(self.items[index])
        try:
            return self.items[index.__index__()]
        except IndexError as e:
            raise IndexError(f"ItemPage index out of range: {index}") from e
        except (TypeError, AttributeError) as e:
            raise TypeError(
                f"ItemPage indices must be objects supporting '__index__' or 'slices', not '{type(index).__name__}'"
            ) from e

    def __reversed__(self) -> Self:
        return self.preserve_metadata_with_items(list(reversed(self.items)))

    # Type safety for merging collections is not enforced at runtime, only through static typing
    # The responsibility for ensuring type compatibility between collections remains with the caller
    def __add__(self, other: Self) -> Self:
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__.__name__}' and '{type(other).__name__}'"
            )
        # Considered adding validation for non-adjacent/overlapping pages but decided against it:
        # 1. Such validation would be complex and potentially unreliable
        # 2. Simplicity and flexibility are prioritized over strict pagination enforcement
        # 3. Responsibility for correct page merging is delegated to the caller
        # NOTE: When merging pages, pagination metadata (`offset`/`limit`) may become inconsistent
        # with the actual content, especially for non-adjacent or overlapping pages
        first, second = (self, other) if self.offset <= other.offset else (other, self)
        combined_items = first.items + second.items
        time_from_ranges = [t for t in (first.time_from, second.time_from) if t is not None]
        time_to_ranges = [t for t in (first.time_to, second.time_to) if t is not None]
        # fmt: off
        return self.__class__.model_construct(
            items=combined_items, offset=first.offset, limit=len(combined_items),
            time_from=min(time_from_ranges) if time_from_ranges else None,
            time_to=max(time_to_ranges) if time_to_ranges else None,
        )
        # fmt: on

    @field_validator(RAW_RESPONSE_ITEMS_KEY, mode="before")
    def normalize_items(cls, items: Any) -> List[Dict[str, Any]]:
        """Normalize the items collection from FACEIT API response.

        This validator ensures consistent structure of items by:
        1. Validating that `items` is a list of dictionaries
        2. Flattening single-key dictionaries when they contain nested objects
           (common in FACEIT API responses, especially in `matches_stats` endpoint)
        """
        if not isinstance(items, list):
            raise ValueError(f"Expected '{RAW_RESPONSE_ITEMS_KEY}' to be a list, got {type(items).__name__}")

        def normalize_item(idx: int, item: Any) -> Dict[str, Any]:
            if not isinstance(item, dict):
                raise ValueError(f"Element at index {idx} must be a dictionary, got {type(item).__name__}")

            if len(item) == 1:  # Flatten single-item dictionaries
                _, value = next(iter(item.items()))
                if isinstance(value, dict):
                    return value

            return item

        return [normalize_item(i, item) for i, item in enumerate(items)]
