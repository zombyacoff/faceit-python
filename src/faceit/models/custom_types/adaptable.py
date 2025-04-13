from __future__ import annotations

import typing as t

from pydantic import AnyHttpUrl, GetCoreSchemaHandler, RootModel
from pydantic_core import core_schema

from ._utils import build_validatable_string_type_schema

_T = t.TypeVar("_T")

if t.TYPE_CHECKING:
    _R = t.TypeVar("_R")


@t.final
class ResponseContainer(RootModel[t.Dict[str, _T]]):
    __slots__ = ()

    def items(self) -> t.ItemsView[str, _T]:
        return self.root.items()

    def keys(self) -> t.KeysView[str]:
        return self.root.keys()

    def values(self) -> t.ValuesView[_T]:
        return self.root.values()

    def __getattr__(self, name: str) -> t.Optional[_T]:
        return self.root.get(name)

    def __iter__(self) -> t.Generator[t.Tuple[str, _T], None, None]:
        yield from self.items()

    def __getitem__(self, key: str) -> _T:
        return self.root[key]

    @t.overload
    def get(self, key: str, /) -> t.Optional[_T]: ...

    @t.overload
    def get(self, key: str, /, default: _R) -> t.Union[_T, _R]: ...

    def get(self, key: str, /, default: t.Any = None) -> t.Any:
        return self.root.get(key, default)


@t.final
class LangFormattedAnyHttpUrl:
    __slots__ = ()

    DEFAULT_LANG = "en"

    @classmethod
    def validate(cls, value: str) -> AnyHttpUrl:
        try:
            return AnyHttpUrl(
                value.format(lang=cls.DEFAULT_LANG)
                if "{lang}" in value
                else value
            )
        except ValueError as e:
            raise ValueError(f"Invalid URL: {e}") from e

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: t.Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        del source_type, handler
        return build_validatable_string_type_schema(cls)


@t.final
class NullableList(t.List[_T]):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: t.Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        del source_type, handler
        # fmt: off
        return core_schema.union_schema([
            core_schema.is_instance_schema(cls),
            core_schema.chain_schema([
                core_schema.union_schema([
                    core_schema.none_schema(),
                    core_schema.str_schema(max_length=0),
                ]),
                core_schema.no_info_plain_validator_function(lambda _: []),
            ]),
        ])
        # fmt: on
