from __future__ import annotations

import typing

from pydantic import AfterValidator, AnyHttpUrl, GetCoreSchemaHandler, RootModel
from pydantic_core import core_schema
from pydantic_extra_types.country import CountryAlpha2
from typing_extensions import Annotated, TypeAlias

from faceit.types import _R, _T

# TODO: Integrate this type alias into all data models in the future
CountryCode: TypeAlias = Annotated[
    # I assume that there must be a better implementation than this.
    # It is necessary to study this issue in more detail.
    CountryAlpha2, AfterValidator(lambda x: typing.cast("str", x).lower())  # noqa: TC008
]
"""
Type alias for country codes that are always validated and converted to lowercase.
Used because Faceit API requires country codes to be in lowercase.
"""


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

    def __getattr__(self, name: str) -> typing.Optional[_T]:
        return self.root.get(name)

    def __iter__(self) -> typing.Generator[typing.Tuple[str, _T], None, None]:  # noqa: PYI058
        yield from self.items()

    def __getitem__(self, key: str) -> _T:
        return self.root[key]


@typing.final
class LangFormattedAnyHttpUrl:
    __slots__ = ()

    _LANG_PLACEHOLDER: typing.ClassVar = "{lang}"

    @classmethod
    def _validate(cls, value: str) -> AnyHttpUrl:
        return AnyHttpUrl(
            "/".join(v for v in value.split("/") if v != cls._LANG_PLACEHOLDER)
        )

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _: typing.Type[typing.Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.union_schema([
            core_schema.str_schema(max_length=0),
            core_schema.no_info_after_validator_function(cls._validate, handler(str)),
        ])


@typing.final
class NullableList(typing.List[_T]):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: typing.Type[typing.Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_before_validator_function(
            lambda x: x or [],
            core_schema.list_schema(
                # NOTE: Current implementation relies on type
                # argument extraction which may be fragile.
                handler.generate_schema(typing.get_args(source_type)[0])
            ),
        )
