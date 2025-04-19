from __future__ import annotations

import typing as t
from abc import ABC, abstractmethod
from uuid import UUID

from faceit._utils import is_valid_uuid, representation

from ._utils import build_validatable_string_type_schema

if t.TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema

    from faceit._typing import Self


class _BaseFaceitUUIDValidator(ABC):
    __slots__ = ()

    _PREFIX: t.ClassVar = ""
    _SUFFIX: t.ClassVar = ""

    @classmethod
    @abstractmethod
    def _validate(cls, value: str, /) -> Self:
        raise NotImplementedError

    @classmethod
    def _remove_prefix_and_suffix(cls, value: str, /) -> str:
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
    def __get_pydantic_core_schema__(
        cls, source_type: t.Type[t.Any], handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        del source_type, handler
        return build_validatable_string_type_schema(
            UUID,
            lambda value: cls._validate(cls._remove_prefix_and_suffix(value)),
        )


# The inconsistency was discovered when verifying account friend lists,
# where some UUIDs would fail validation due to this unexpected suffix.
class BaseFaceitID(_BaseFaceitUUIDValidator, ABC):
    __slots__ = ()

    _SUFFIX = "gui"


@t.final
class FaceitID(UUID, BaseFaceitID):
    __slots__ = ()

    @classmethod
    def _validate(cls, value: str, /) -> Self:
        if is_valid_uuid(value):
            return cls(value)
        raise ValueError(
            f"Invalid {cls.__name__}: '{value}' is not a valid UUID format."
        )


@representation(use_str=True)
class _FaceitIDWithUniquePrefix(str, BaseFaceitID, ABC):
    __slots__ = ()

    UNIQUE_PREFIX: t.ClassVar[str]

    def __init_subclass__(cls, *, prefix: str, **kwargs: t.Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.UNIQUE_PREFIX = prefix

    @classmethod
    def _validate(cls, value: str, /) -> Self:
        if not value.startswith(cls.UNIQUE_PREFIX):
            raise ValueError(
                f"Invalid {cls.__name__}: "
                f"'{value}' must start with '{cls.UNIQUE_PREFIX}'"
            )
        if not is_valid_uuid(value[len(cls.UNIQUE_PREFIX) :]):
            raise ValueError(
                f"Invalid {cls.__name__}: "
                f"'{value}' contains invalid UUID part. "
            )
        return cls(value)


@t.final
class FaceitTeamID(_FaceitIDWithUniquePrefix, prefix="team-"):
    __slots__ = ()


@t.final
class FaceitMatchID(_FaceitIDWithUniquePrefix, prefix="1-"):
    __slots__ = ()
