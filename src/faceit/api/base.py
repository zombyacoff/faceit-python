from __future__ import annotations

import logging
import warnings
from abc import ABC
from dataclasses import dataclass
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    TypedDict,
    TypeVar,
    cast,
    final,
)

from pydantic import ValidationError

from faceit.http import Endpoint
from faceit.models import ItemPage
from faceit.types import (
    _T,
    ClientT,
    ModelT,
    RawAPIItem,
    RawAPIPageResponse,
    RawAPIResponse,
)
from faceit.utils import warn_stacklevel

if TYPE_CHECKING:
    from collections.abc import Mapping

    _ResponseT = TypeVar("_ResponseT", bound=RawAPIResponse)

_logger = logging.getLogger(__name__)

# Temporary placeholder type for unimplemented models.
# Serves as a stub during development and should be replaced with
# concrete models as implementation progresses.
ModelPlaceholder: None = None


@final
class RequestPayload(TypedDict):
    endpoint: Endpoint
    params: Mapping[str, Any]


@final
@dataclass(eq=False, frozen=True)
class MappedValidatorConfig(Generic[_T, ModelT]):
    validator_map: Mapping[_T, type[ModelT]]
    key_name: str = "key"
    default_validator: type[ModelT] | None = None


# TODO: Refactor the base resource class if/when support for resources
# other than Data is required, since the current implementation is
# too Data-centric.
class BaseResource(ABC, Generic[ClientT]):
    __slots__ = (
        "_client",
        "_raw",
        "_strict_validation",
    )

    if TYPE_CHECKING:
        PATH: ClassVar[Endpoint]

    _PARAM_NAME_MAP: ClassVar[Mapping[str, str]] = MappingProxyType({
        "start": "from",
        "category": "type",
    })

    def __init__(
        self,
        client: ClientT,
        *,
        raw: bool,
        strict_validation: bool = True,  # IDEA: Should this be configured in the aggregator?
    ) -> None:
        self._client = client
        self._raw = raw
        self._strict_validation = strict_validation

    def __init_subclass__(
        cls,
        resource_path: str | None = None,
        **kwargs: Any,
    ) -> None:
        if hasattr(cls, "PATH"):
            return
        if resource_path is None:
            msg = (
                f"Class {cls.__name__} requires 'path' "
                "parameter or a parent with 'PATH' defined."
            )
            raise TypeError(msg)
        cls.PATH = Endpoint(resource_path)
        super().__init_subclass__(**kwargs)

    @property
    def is_raw(self) -> bool:
        return self._raw

    @property
    def strict_validation_enabled(self) -> bool:
        return self._strict_validation

    def _process_item(
        self,
        response: RawAPIItem,
        key: _T,
        config: MappedValidatorConfig[_T, ModelT],
    ) -> RawAPIItem | ModelT:
        if self._raw:
            return response
        return self._validate_response(
            response,
            config.validator_map.get(key, config.default_validator),
        )

    def _process_page(
        self,
        response: RawAPIPageResponse,
        key: _T,
        config: MappedValidatorConfig[_T, ModelT],
    ) -> RawAPIPageResponse | ItemPage[ModelT]:
        if self._raw:
            return response

        validator = config.validator_map.get(key, config.default_validator)
        if validator is None:
            page_validator = None
        else:
            page_validator = cast(
                "type[ItemPage[ModelT]]",
                # Suppressing type checking warning because we're using a
                # dynamic runtime subscript `ItemPage` is being subscripted
                # with a variable (`validator`) which mypy cannot statically verify
                ItemPage[validator],  # type: ignore[valid-type]
            )

        return self._validate_response(
            response,
            page_validator,
            warn_msg=(
                f"No model defined for {config.key_name} {key!r}. "
                "Validation and model parsing are unavailable. "
                "Using raw response."
            ),
        )

    def _validate_response(
        self,
        response: _ResponseT,
        validator: type[ModelT] | None,
        /,
        *,
        warn_msg: str | None = None,
    ) -> _ResponseT | ModelT:
        if self._raw:
            return response
        if validator is None:
            # TODO: Better message for missing validator
            default_warn_msg = (
                "No model defined for this response. Validation and model "
                "parsing are unavailable. Use the raw version for explicit, "
                "unprocessed data."
            )
            msg = default_warn_msg if warn_msg is None else warn_msg
            warnings.warn(msg, stacklevel=warn_stacklevel())
            return response
        try:
            return validator.model_validate(response)
        except ValidationError:
            _logger.exception("Validation failed for %s", validator.__name__)
            if self.strict_validation_enabled:
                raise
            warnings.warn(
                "Validation failed but strict mode disabled. Raw response returned.",
                RuntimeWarning,
                stacklevel=2,  # ???: What should be the stack level in this case
            )
            return response

    @classmethod
    def _build_params(cls, **params: Any) -> dict[str, Any]:
        return {
            cls._PARAM_NAME_MAP.get(key, key): value
            for key, value in params.items()
            if value is not None
        }
