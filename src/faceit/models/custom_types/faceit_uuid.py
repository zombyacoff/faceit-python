from __future__ import annotations

import typing as t
from abc import ABC, abstractmethod
from uuid import UUID

import typing_extensions as te
from pydantic_core import core_schema

from faceit.utils import is_valid_uuid, representation

if t.TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler


class _BaseFaceitUUIDValidator(ABC):
    __slots__ = ()

    _PREFIX: t.ClassVar = ""
    _SUFFIX: t.ClassVar = ""

    @classmethod
    @abstractmethod
    def _validate(cls, value: str, /) -> te.Self:
        raise NotImplementedError

    @classmethod
    def __remove_prefix_and_suffix(cls, value: str, /) -> str:
        if not cls._PREFIX and not cls._SUFFIX:
            return value

        start = (
            len(cls._PREFIX)
            if cls._PREFIX and value.startswith(cls._PREFIX)
            else 0
        )
        end = (
            -len(cls._SUFFIX)
            if cls._SUFFIX and value.endswith(cls._SUFFIX)
            else None
        )

        if start == 0 and end is None:
            return value

        return value[start:end]

    @classmethod
    def __pydantic_parse(cls, value: str, /) -> te.Self:
        return cls._validate(cls.__remove_prefix_and_suffix(value))

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: t.Type[t.Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        del source_type
        return core_schema.union_schema([
            core_schema.str_schema(max_length=0),
            core_schema.no_info_after_validator_function(
                cls.__pydantic_parse, handler(str)
            ),
        ])


# The inconsistency was discovered when verifying account friend lists,
# where some UUIDs would fail validation due to this unexpected suffix.
class BaseFaceitID(_BaseFaceitUUIDValidator):
    __slots__ = ()

    _SUFFIX = "gui"


@t.final
class FaceitID(UUID, BaseFaceitID):
    __slots__ = ()

    @classmethod
    def _validate(cls, value: str, /) -> te.Self:
        if is_valid_uuid(value):
            return cls(value)
        raise ValueError(
            f"Invalid {cls.__name__}: {value!r} is not a valid UUID format."
        )


@representation(use_str=True)
class _FaceitIDWithUniquePrefix(str, BaseFaceitID, ABC):
    __slots__ = ()

    if t.TYPE_CHECKING:
        UNIQUE_PREFIX: t.ClassVar[str]

    def __init_subclass__(cls, prefix: str, **kwargs: t.Any) -> None:
        cls.UNIQUE_PREFIX = prefix
        super().__init_subclass__(**kwargs)

    @classmethod
    def _validate(cls, value: str, /) -> te.Self:
        if not value.startswith(cls.UNIQUE_PREFIX):
            raise ValueError(
                f"Invalid {cls.__name__}: "
                f"{value!r} must start with {cls.UNIQUE_PREFIX!r}"
            )
        if not is_valid_uuid(value[len(cls.UNIQUE_PREFIX) :]):
            raise ValueError(
                f"Invalid {cls.__name__}: "
                f"{value!r} contains invalid UUID part."
            )
        return cls(value)


@t.final
class FaceitTeamID(_FaceitIDWithUniquePrefix, prefix="team-"):
    __slots__ = ()


@t.final
class FaceitMatchID(_FaceitIDWithUniquePrefix, prefix="1-"):
    __slots__ = ()
