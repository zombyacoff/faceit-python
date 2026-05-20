from __future__ import annotations

import re
from abc import ABC
from datetime import datetime, timezone
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Final,
    TypeAlias,
    final,
    overload,
)

from pydantic import (
    AfterValidator,
    BeforeValidator,
    RootModel,
    model_validator,
)
from pydantic_core import core_schema
from typing_extensions import Self

from faceit.types import _R, _T, UrlOrEmpty

if TYPE_CHECKING:
    from collections.abc import ItemsView, Iterator, KeysView, ValuesView

_LANG_PLACEHOLDER: Final = "{lang}"
_LANG_PATTERN: Final = re.compile(rf"/?{re.escape(_LANG_PLACEHOLDER)}/?")

LangFormattedAnyHttpUrl: TypeAlias = Annotated[
    UrlOrEmpty,
    BeforeValidator(
        lambda x: _LANG_PATTERN.sub("/", x).replace("//", "/").strip("/") if x else ""
    ),
]
NullableList: TypeAlias = Annotated[
    list[_T],
    BeforeValidator(lambda x: x or []),
]
# NOTE: Type alias for country codes that are always validated and converted to lowercase
# Used because Faceit API requires country codes to be in lowercase
#
# TODO: Integrate this type alias into all data models in the future
CountryCode: TypeAlias = Annotated[
    str,  # TODO: Should be ISO 3166-1 alpha-2 enum
    AfterValidator(lambda x: x.lower()),
]


class _BaseTimestamp(int, ABC):
    __slots__ = ()

    if TYPE_CHECKING:
        _UNITS_PER_SEC: ClassVar[int]

    def __init_subclass__(cls, units_per_sec: int, **kwargs: Any) -> None:
        cls._UNITS_PER_SEC = units_per_sec
        return super().__init_subclass__(**kwargs)

    def to_datetime(self) -> datetime:
        return datetime.fromtimestamp(self / self._UNITS_PER_SEC, tz=timezone.utc)

    @classmethod
    def from_datetime(cls, dt: datetime, /) -> Self:
        return cls(round(dt.timestamp() * cls._UNITS_PER_SEC))

    @classmethod
    def __get_pydantic_core_schema__(cls, *_: Any, **__: Any) -> core_schema.CoreSchema:
        return core_schema.chain_schema([
            core_schema.int_schema(ge=0),
            core_schema.no_info_after_validator_function(cls, core_schema.any_schema()),
        ])


@final
class TimestampMs(_BaseTimestamp, units_per_sec=1000):
    @property
    def as_sec(self) -> TimestampSec:
        return TimestampSec(self // 1000)


@final
class TimestampSec(_BaseTimestamp, units_per_sec=1):
    @property
    def as_ms(self) -> TimestampMs:
        return TimestampMs(self * 1000)


TimestampLike: TypeAlias = TimestampSec | TimestampMs | int
NotStrictTimestampMs: TypeAlias = TimestampMs | int
NotStrictTimestampSec: TypeAlias = TimestampSec | int


_INJECTED_KEY: Final = "injected_key"


@final
class ResponseContainer(RootModel[dict[str, _T]]):
    __slots__ = ()

    def items(self) -> ItemsView[str, _T]:
        return self.root.items()

    def keys(self) -> KeysView[str]:
        return self.root.keys()

    def values(self) -> ValuesView[_T]:
        return self.root.values()

    @overload
    def get(self, key: str, /) -> _T | None: ...

    @overload
    def get(self, key: str, /, default: _R) -> _T | _R: ...

    def get(self, key: str, /, default: _R | None = None) -> _T | _R | None:
        return self.root.get(key, default)

    def __getattr__(self, name: str) -> _T:
        if name in self.root:
            return self.root[name]
        msg = f"{self.__class__.__name__!r} object has no attribute {name!r}"
        raise AttributeError(msg)

    def __iter__(self) -> Iterator[str]:  # type: ignore[override]
        yield from self.root

    def __getitem__(self, key: str) -> _T:
        return self.root[key]

    @model_validator(mode="before")
    @classmethod
    def _inject_keys(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        return {
            k: {**v, _INJECTED_KEY: k} if isinstance(v, dict) else v
            for k, v in data.items()
        }
