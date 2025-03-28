from abc import ABC, abstractmethod
from functools import lru_cache
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generator,
    ItemsView,
    KeysView,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    ValuesView,
    final,
    overload,
)
from uuid import UUID

from pydantic import AnyHttpUrl, RootModel
from pydantic_core import core_schema

from faceit.types import Self, TypeVar
from faceit.utils import is_valid_uuid

_T = TypeVar("_T")
_R = TypeVar("_R")


@final
class ResponseContainer(RootModel[Dict[str, _T]]):
    """Dictionary-like container with attribute access to keys.

    Provides a convenient interface for accessing dictionary values as attributes
    while maintaining standard dictionary functionality.
    """

    @property
    def items(self) -> ItemsView[str, _T]:
        return self.root.items()

    @property
    def keys(self) -> KeysView[str]:
        return self.root.keys()

    @property
    def values(self) -> ValuesView[_T]:
        return self.root.values()

    def __getattr__(self, name: str) -> Optional[_T]:
        return self.root.get(name)

    def __iter__(self) -> Generator[Tuple[str, _T], None, None]:
        yield from self.items

    def __getitem__(self, key: str) -> _T:
        return self.root[key]

    @overload
    def get(self, key: str, /) -> Optional[_T]: ...
    @overload
    def get(self, key: str, /, default: _R) -> Union[_T, _R]: ...
    def get(self, key: str, /, default: Any = None) -> Any:
        return self.root.get(key, default)


def _build_validatable_string_type_schema(
    obj: Type[Any], validator: Optional[Callable[..., Any]] = None
) -> core_schema.CoreSchema:
    """Create a validation schema for string-based custom types.

    Constructs a union schema that handles direct instances, empty strings,
    and string values that require validation.
    """
    if validator is None:
        # If no explicit `validator` is provided,
        # try to use the object's validate method
        if not hasattr(obj, "validate"):
            raise ValueError(
                f"No validator provided and {obj.__name__} has no 'validate' method. "
                f"Either provide a validator function or implement a 'validate' method."
            )
        validator = obj.validate
    # fmt: off
    return core_schema.union_schema([
        core_schema.is_instance_schema(obj),
        core_schema.str_schema(max_length=0),
        core_schema.chain_schema([
            core_schema.str_schema(),
            core_schema.no_info_plain_validator_function(validator),
        ]),
    ])
    # fmt: on


class _BaseFaceitUUIDValidator(ABC):
    """Base implementation for FACEIT UUID handling.

    Provides core functionality for `UUID` validation with custom `prefix`/`suffix` handling.
    This class is not meant to be used directly but serves as a foundation for specialized
    `UUID` classes.
    """

    _PREFIX = _SUFFIX = ""

    @classmethod
    @lru_cache(maxsize=100)
    def _remove_prefix_and_suffix(cls, value: str) -> str:
        if not cls._PREFIX and not cls._SUFFIX:
            return value

        start = len(cls._PREFIX) if cls._PREFIX and value.startswith(cls._PREFIX) else 0
        end = -len(cls._SUFFIX) if cls._SUFFIX and value.endswith(cls._SUFFIX) else None

        if start == 0 and end is None:
            return value

        return value[start:end]

    @classmethod
    @abstractmethod
    def validate(cls, value: str) -> Self: ...

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> core_schema.CoreSchema:
        return _build_validatable_string_type_schema(UUID, lambda v: cls.validate(cls._remove_prefix_and_suffix(v)))


class BaseFaceitID(_BaseFaceitUUIDValidator, ABC):
    """Base class for FACEIT platform `UUID` identifiers with custom formatting.

    Handles the `gui` suffix that appears in some FACEIT UUID formats,
    automatically removing it during validation.
    """

    # The inconsistency was discovered when verifying account friend lists,
    # where some UUIDs would fail validation due to this unexpected suffix.

    _SUFFIX = "gui"


@final
class FaceitID(UUID, BaseFaceitID):
    """`UUID` implementation for standard FACEIT IDs without special prefixes.

    Primarily used for player identifiers.

    The entire input value must be a valid `UUID` format.
    """

    @classmethod
    def validate(cls, value: str) -> Self:
        if not is_valid_uuid(value):
            raise ValueError(f"Invalid {cls.__name__}: '{value}' is not a valid UUID format.")
        return cls(value)


class _FaceitIDWithUniquePrefix(str, BaseFaceitID, ABC):
    """Base class for FACEIT UUIDs that include a specific prefix.

    Validates that the string starts with the required prefix and contains
    a valid `UUID` after the prefix.
    """

    UNIQUE_PREFIX: ClassVar[str]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self)!r})"

    @classmethod
    def validate(cls, value: str) -> Self:
        if not value.startswith(cls.UNIQUE_PREFIX):
            raise ValueError(f"Invalid {cls.__name__}: '{value}' must start with '{cls.UNIQUE_PREFIX}'")

        if not is_valid_uuid(value[len(cls.UNIQUE_PREFIX) :]):
            raise ValueError(f"Invalid {cls.__name__}: '{value}' contains invalid UUID part. ")

        return cls(value)


@final
class FaceitTeamID(_FaceitIDWithUniquePrefix):
    """UUID implementation for FACEIT team identifiers.

    Team IDs always start with the `team-` prefix.
    """

    UNIQUE_PREFIX = "team-"


@final
class FaceitMatchID(_FaceitIDWithUniquePrefix):
    """UUID implementation for FACEIT match identifiers.

    Match IDs always start with the `1-` prefix.
    """

    UNIQUE_PREFIX = "1-"


@final
class LangFormattedHttpUrl:
    """HTTP URL with language formatting support.

    Handles URLs containing `{lang}` placeholders by substituting
    the default language code.
    """

    DEFAULT_LANG = "en"

    @classmethod
    @lru_cache(maxsize=100)
    def validate(cls, value: str) -> AnyHttpUrl:
        try:
            return AnyHttpUrl(value.format(lang=cls.DEFAULT_LANG) if "{lang}" in value else value)
        except ValueError as e:
            raise ValueError(f"Invalid URL: {e}")

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> core_schema.CoreSchema:
        return _build_validatable_string_type_schema(cls)


@final
class NullableList(List[_T]):
    """List type that converts None or empty strings to an empty list."""

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> core_schema.CoreSchema:
        # fmt: off
        return core_schema.union_schema([
            core_schema.is_instance_schema(cls),
            core_schema.list_schema(core_schema.any_schema(), min_length=0, max_length=0),
            core_schema.chain_schema([
                core_schema.union_schema([
                    core_schema.none_schema(),
                    core_schema.str_schema(max_length=0),
                ]),
                core_schema.no_info_plain_validator_function(lambda _: []),  # transform to empty list
            ]),
        ])
        # fmt: on
