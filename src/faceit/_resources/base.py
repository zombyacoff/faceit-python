from __future__ import annotations

import logging
import typing as t
from abc import ABC
from dataclasses import dataclass
from warnings import warn

from pydantic import ValidationError
from strenum import StrEnum

from faceit._typing import ClientT, ModelT, RawAPIPageResponse, RawAPIResponse
from faceit.http import Endpoint
from faceit.models import ItemPage

from .pagination import (
    AsyncPageIterator,
    SyncPageIterator,
    TimestampPaginationConfig,
)

if t.TYPE_CHECKING:
    _ResponseT = t.TypeVar("_ResponseT", bound=RawAPIResponse)

_logger = logging.getLogger(__name__)

_KT = t.TypeVar("_KT")

# Temporary placeholder type for unimplemented models.
# Serves as a stub during development and should be replaced with
# concrete models as implementation progresses.
ModelPlaceholder: None = None


@t.final
class RequestPayload(t.TypedDict):
    endpoint: Endpoint
    params: t.Dict[str, t.Any]


@t.final
class MappedValidatorConfig(t.NamedTuple, t.Generic[_KT, ModelT]):
    validator_map: t.Dict[_KT, t.Type[ModelT]]
    is_paged: bool
    key_name: str = "key"


class FaceitResourcePath(StrEnum):
    CHAMPIONSHIPS = "championships"
    MATCHES = "matches"
    PLAYERS = "players"
    RANKINGS = "rankings"
    TEAMS = "teams"


# TODO: Refactor the base resource class if/when support for resources
# other than Data is required, since the current implementation is
# too Data-centric.
@dataclass(eq=False, frozen=True)
class BaseResource(t.Generic[ClientT], ABC):
    __slots__ = ("_client", "_raw")

    _client: ClientT
    _raw: bool

    _sync_page_iterator: t.ClassVar = SyncPageIterator
    _async_page_iterator: t.ClassVar = AsyncPageIterator
    _timestamp_cfg: t.ClassVar = TimestampPaginationConfig

    _PARAM_NAME_MAP: t.ClassVar[t.Dict[str, str]] = {
        "start": "from",
        "category": "type",
    }

    PATH: t.ClassVar[Endpoint]

    def __init_subclass__(
        cls,
        *,
        resource_path: t.Optional[FaceitResourcePath] = None,
        **kwargs: t.Any,
    ) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "PATH"):
            return
        if resource_path is None:
            raise TypeError(
                f"Class {cls.__name__} requires 'path' "
                f"parameter or a parent with 'PATH' defined."
            )
        cls.PATH = Endpoint(resource_path)

    @property
    def raw(self) -> bool:
        return self._raw

    # NOTE: These overloads are necessary as this function directly returns in resource
    # methods, where typing must be strict for public API. Current implementation
    # is sufficient, though alternative typing approaches could be considered.

    @t.overload
    def _process_response_with_mapped_validator(
        self,
        response: RawAPIPageResponse,
        key: _KT,
        config: MappedValidatorConfig[_KT, ModelT],
        /,
    ) -> t.Union[ModelT, RawAPIPageResponse]: ...

    @t.overload
    def _process_response_with_mapped_validator(
        self,
        response: RawAPIPageResponse,
        key: _KT,
        config: MappedValidatorConfig[_KT, ModelT],
        /,
    ) -> t.Union[ItemPage[ModelT], RawAPIPageResponse]: ...

    def _process_response_with_mapped_validator(
        self,
        response: RawAPIPageResponse,
        key: _KT,
        config: MappedValidatorConfig[_KT, ModelT],
        /,
    ) -> t.Union[ModelT, ItemPage[ModelT], RawAPIPageResponse]:
        _logger.debug(
            "Processing response with mapped validator for key: %s", key
        )

        validator = config.validator_map.get(key)
        if validator is None:
            warn(
                f"No model defined for {config.key_name} '{key}'. "
                f"Consider using the raw response.",
                UserWarning,
                stacklevel=5,
            )
            return response

        # Suppressing type checking warning because we're using a
        # dynamic runtime subscript `ItemPage` is being subscripted
        # with a variable (`validator`) which mypy cannot statically verify
        return self._validate_response(
            response,
            t.cast(t.Type[ModelT], ItemPage[validator])  # type: ignore[valid-type]
            if config.is_paged
            else validator,
        )

    def _validate_response(
        self,
        response: _ResponseT,
        validator: t.Optional[t.Type[ModelT]],
        /,
    ) -> t.Union[_ResponseT, ModelT]:
        if self._raw:
            return response

        if validator is None:
            warn(
                "No model defined for this response. Validation and model "
                "parsing are unavailable. Use the raw version for explicit, "
                "unprocessed data.",
                UserWarning,
                stacklevel=5,
            )
            return response

        try:
            return validator.model_validate(response)
        except ValidationError:
            _logger.exception("Validation failed for %s", validator.__name__)
            return response

    @classmethod
    def _build_params(cls, **params: t.Any) -> t.Dict[str, t.Any]:
        return {
            cls._PARAM_NAME_MAP.get(key, key): value
            for key, value in params.items()
            if value is not None
        }
