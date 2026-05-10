from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from uuid import UUID

from pydantic_core import core_schema
from typing_extensions import Self, TypeAlias

from faceit.types import EmptyString
from faceit.utils import is_valid_uuid, representation

if typing.TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler


class _BaseFaceitUUIDValidator(ABC):
    __slots__ = ()

    _PREFIX: typing.ClassVar = ""
    _SUFFIX: typing.ClassVar = ""

    @classmethod
    @abstractmethod
    def _validate(cls, value: str, /) -> Self:
        raise NotImplementedError

    @classmethod
    def _remove_prefix_and_suffix(cls, value: str, /) -> str:
        if not cls._PREFIX and not cls._SUFFIX:
            return value

        start = (
            len(cls._PREFIX) if cls._PREFIX and value.startswith(cls._PREFIX) else None
        )
        end = -len(cls._SUFFIX) if cls._SUFFIX and value.endswith(cls._SUFFIX) else None

        if start is None and end is None:
            return value

        return value[start:end]

    @classmethod
    def __get_pydantic_core_schema__(  # noqa: PLW3201
        cls, _: typing.Type[typing.Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.union_schema([
            core_schema.no_info_after_validator_function(
                lambda v: cls._validate(cls._remove_prefix_and_suffix(v)),
                handler(str),
                serialization=core_schema.to_string_ser_schema(when_used="json"),
            )
        ])


# The inconsistency was discovered when verifying account friend lists,
# where some UUIDs would fail validation due to this unexpected suffix.
class BaseFaceitID(_BaseFaceitUUIDValidator):
    __slots__ = ()

    _SUFFIX = "gui"


@typing.final
class FaceitID(UUID, BaseFaceitID):
    __slots__ = ()

    @classmethod
    def _validate(cls, value: str, /) -> Self:
        if is_valid_uuid(value):
            return cls(str(value))
        raise ValueError(
            f"Invalid {cls.__name__}: {value!r} is not a valid UUID format."
        )


MaybeFaceitID: TypeAlias = typing.Union[FaceitID, EmptyString]


@representation(use_str=True)
class _FaceitIDWithUniquePrefix(str, BaseFaceitID, ABC):
    __slots__ = ()

    if typing.TYPE_CHECKING:
        UNIQUE_PREFIX: typing.ClassVar[str]

    def __init_subclass__(cls, prefix: str, **kwargs: typing.Any) -> None:
        cls.UNIQUE_PREFIX = prefix
        super().__init_subclass__(**kwargs)

    @classmethod
    def _validate(cls, value: str, /) -> Self:
        if not value.startswith(cls.UNIQUE_PREFIX):
            msg = f"Invalid {cls.__name__}: {value!r} must start with {cls.UNIQUE_PREFIX!r}"
            raise ValueError(msg)
        if not is_valid_uuid(value[len(cls.UNIQUE_PREFIX) :]):
            msg = f"Invalid {cls.__name__}: {value!r} contains invalid UUID part."
            raise ValueError(msg)
        return cls(value)


@typing.final
class FaceitTeamID(_FaceitIDWithUniquePrefix, prefix="team-"):
    __slots__ = ()


@typing.final
class FaceitMatchID(_FaceitIDWithUniquePrefix, prefix="1-"):
    __slots__ = ()
