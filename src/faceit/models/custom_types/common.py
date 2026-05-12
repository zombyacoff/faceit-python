from __future__ import annotations

import re
import typing
from abc import ABC
from datetime import datetime, timezone

from pydantic import (
    AfterValidator,
    BeforeValidator,
    GetCoreSchemaHandler,
    RootModel,
    model_validator,
)
from pydantic_core import core_schema
from typing_extensions import Annotated, Self, TypeAlias

from faceit.types import _R, _T, UrlOrEmpty

_INJECTED_KEY: typing.Final = "injected_key"
_LANG_PLACEHOLDER: typing.Final = "{lang}"
_LANG_PATTERN: typing.Final = re.compile(rf"/?{re.escape(_LANG_PLACEHOLDER)}/?")

LangFormattedAnyHttpUrl: TypeAlias = Annotated[
    UrlOrEmpty,
    BeforeValidator(
        lambda x: _LANG_PATTERN.sub("/", x).replace("//", "/").strip("/") if x else ""
    ),
]
NullableList: TypeAlias = Annotated[
    typing.List[_T],
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

    if typing.TYPE_CHECKING:
        _UNITS_PER_SEC: typing.ClassVar[int]

    def __init_subclass__(cls, units_per_sec: int, **kwargs: typing.Any) -> None:
        cls._UNITS_PER_SEC = units_per_sec
        return super().__init_subclass__(**kwargs)

    def to_datetime(self) -> datetime:
        return datetime.fromtimestamp(self / self._UNITS_PER_SEC, tz=timezone.utc)

    @classmethod
    def from_datetime(cls, dt: datetime, /) -> Self:
        return cls(round(dt.timestamp() * cls._UNITS_PER_SEC))

    @classmethod
    def _validate(cls, value: int, /) -> Self:
        if value >= 0:
            return cls(value)
        msg = f"Value {value} is negative. Timestamp cannot be negative"
        raise ValueError(msg)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _: typing.Type[typing.Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(cls._validate, handler(int))


@typing.final
class TimestampMs(_BaseTimestamp, units_per_sec=1000):
    @property
    def as_sec(self) -> TimestampSec:
        return TimestampSec(self // 1000)


@typing.final
class TimestampSec(_BaseTimestamp, units_per_sec=1):
    @property
    def as_ms(self) -> TimestampMs:
        return TimestampMs(self * 1000)


TimestampLike: TypeAlias = typing.Union[TimestampSec, TimestampMs, int]
NotStrictTimestampMs: TypeAlias = typing.Union[TimestampMs, int]
NotStrictTimestampSec: TypeAlias = typing.Union[TimestampSec, int]


@typing.final
class ResponseContainer(RootModel[typing.Dict[str, _T]]):
    __slots__ = ()

    def items(self) -> typing.ItemsView[str, _T]:
        return self.root.items()

    def keys(self) -> typing.KeysView[str]:
        return self.root.keys()

    def values(self) -> typing.ValuesView[_T]:
        return self.root.values()

    @typing.overload
    def get(self, key: str, /) -> typing.Optional[_T]: ...

    @typing.overload
    def get(self, key: str, /, default: _R) -> typing.Union[_T, _R]: ...

    def get(
        self, key: str, /, default: typing.Optional[_R] = None
    ) -> typing.Union[_T, _R, None]:
        return self.root.get(key, default)

    def __getattr__(self, name: str) -> _T:
        if name in self.root:
            return self.root[name]
        msg = f"'{self.__class__.__name__}' object has no attribute '{name}'"
        raise AttributeError(msg)

    def __iter__(self) -> typing.Iterator[str]:  # type: ignore[override]
        yield from self.root

    def __getitem__(self, key: str) -> _T:
        return self.root[key]

    @model_validator(mode="before")
    @classmethod
    def _inject_keys(cls, data: typing.Any) -> typing.Any:
        if not isinstance(data, dict):
            return data
        return {
            k: {**v, _INJECTED_KEY: k} if isinstance(v, dict) else v
            for k, v in data.items()
        }
