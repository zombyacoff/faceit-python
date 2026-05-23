from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias, final
from uuid import UUID

from pydantic_core import core_schema
from typing_extensions import Self

from faceit.types import EmptyString
from faceit.utils import is_valid_uuid, representation

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler


class _BaseFaceitUUIDValidator(ABC):
    __slots__ = ()

    _PREFIX: ClassVar = ""
    _SUFFIX: ClassVar = ""

    @classmethod
    @abstractmethod
    def _validate(cls, value: str, /) -> Self:
        raise NotImplementedError

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            lambda v: cls._validate(
                v.removeprefix(cls._PREFIX).removesuffix(cls._SUFFIX)
            ),
            handler(str),
            serialization=core_schema.to_string_ser_schema(when_used="json"),
        )


# The inconsistency was discovered when verifying account friend lists,
# where some UUIDs would fail validation due to this unexpected suffix
class BaseFaceitID(_BaseFaceitUUIDValidator):
    __slots__ = ()

    _SUFFIX = "gui"


@final
class FaceitID(UUID, BaseFaceitID):
    __slots__ = ()

    @classmethod
    def _validate(cls, value: str, /) -> Self:
        if is_valid_uuid(value):
            return cls(str(value))
        msg = f"Invalid {cls.__name__}: {value!r} is not a valid UUID format."  # type: ignore[unreachable]
        raise ValueError(msg)


MaybeFaceitID: TypeAlias = FaceitID | EmptyString


@representation(use_str=True)
class _FaceitIDWithUniquePrefix(str, BaseFaceitID, ABC):
    __slots__ = ()

    if TYPE_CHECKING:
        UNIQUE_PREFIX: ClassVar[str]

    def __init_subclass__(cls, prefix: str, **kwargs: Any) -> None:
        cls.UNIQUE_PREFIX = prefix
        super().__init_subclass__(**kwargs)

    @classmethod
    def _validate(cls, value: str, /) -> Self:
        if not value.startswith(cls.UNIQUE_PREFIX):
            msg = f"Invalid {cls.__name__}: {value!r} must start with {cls.UNIQUE_PREFIX!r}"
            raise ValueError(msg)
        if not is_valid_uuid(value.removeprefix(cls.UNIQUE_PREFIX)):
            msg = f"Invalid {cls.__name__}: {value!r} contains invalid UUID part."
            raise ValueError(msg)
        return cls(value)


@final
class FaceitMatchID(_FaceitIDWithUniquePrefix, prefix="1-"):
    __slots__ = ()


@final
class FaceitTeamID(_FaceitIDWithUniquePrefix, prefix="team-"):
    __slots__ = ()
