from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import TYPE_CHECKING, Any, ClassVar, final
from uuid import UUID

from faceit._utils import is_valid_uuid

from ._utils import build_validatable_string_type_schema

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema

    from faceit._types import Self


class _BaseFaceitUUIDValidator(ABC):
    __slots__ = ()

    _PREFIX: ClassVar = ""
    _SUFFIX: ClassVar = ""

    @classmethod
    @lru_cache
    def _remove_prefix_and_suffix(cls, value: str) -> str:
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
    @abstractmethod
    def validate(cls, value: str) -> Self: ...

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        del source_type, handler
        return build_validatable_string_type_schema(
            UUID,
            lambda value: cls.validate(cls._remove_prefix_and_suffix(value)),
        )


# The inconsistency was discovered when verifying account friend lists,
# where some UUIDs would fail validation due to this unexpected suffix.
class BaseFaceitID(_BaseFaceitUUIDValidator, ABC):
    __slots__ = ()

    _SUFFIX = "gui"


@final
class FaceitID(UUID, BaseFaceitID):
    __slots__ = ()

    @classmethod
    def validate(cls, value: str) -> Self:
        if not is_valid_uuid(value):
            raise ValueError(
                f"Invalid {cls.__name__}: '{value}' is not a valid UUID format."
            )
        return cls(value)


class _FaceitIDWithUniquePrefix(str, BaseFaceitID, ABC):
    __slots__ = ()

    UNIQUE_PREFIX: ClassVar[str]

    def __init_subclass__(cls, *, unique_prefix: str, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.UNIQUE_PREFIX = unique_prefix

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self}')"

    @classmethod
    def validate(cls, value: str) -> Self:
        if not value.startswith(cls.UNIQUE_PREFIX):
            raise ValueError(
                f"Invalid {cls.__name__}: '{value}' must start with '{cls.UNIQUE_PREFIX}'"
            )

        if not is_valid_uuid(value[len(cls.UNIQUE_PREFIX) :]):
            raise ValueError(
                f"Invalid {cls.__name__}: '{value}' contains invalid UUID part. "
            )

        return cls(value)


@final
class FaceitTeamID(_FaceitIDWithUniquePrefix, unique_prefix="team-"):
    __slots__ = ()


@final
class FaceitMatchID(_FaceitIDWithUniquePrefix, unique_prefix="1-"):
    __slots__ = ()
