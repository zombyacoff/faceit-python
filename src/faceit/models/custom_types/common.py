from __future__ import annotations

import re
import typing

from pydantic import AfterValidator, BeforeValidator, RootModel, model_validator
from typing_extensions import Annotated, TypeAlias

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

# NOTE: Type alias for country codes that are always validated and converted to lowercase.
# Used because Faceit API requires country codes to be in lowercase.
#
# TODO: Integrate this type alias into all data models in the future
CountryCode: TypeAlias = Annotated[
    str,  # TODO: Should be ISO 3166-1 alpha-2 enum
    AfterValidator(lambda x: x.lower()),
]


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
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

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
