from __future__ import annotations

import logging
import typing
from abc import ABC
from dataclasses import dataclass
from types import MappingProxyType
from warnings import warn

from pydantic import ValidationError

from faceit.http import Endpoint
from faceit.models import ItemPage
from faceit.types import (
    _T,
    ClientT,
    ModelT,
    RawAPIPageResponse,
    RawAPIResponse,
)
from faceit.utils import StrEnum

from .pagination import AsyncPageIterator, SyncPageIterator, TimestampPaginationConfig

if typing.TYPE_CHECKING:
    _ResponseT = typing.TypeVar("_ResponseT", bound=RawAPIResponse)

_logger = logging.getLogger(__name__)

# Temporary placeholder type for unimplemented models.
# Serves as a stub during development and should be replaced with
# concrete models as implementation progresses.
ModelPlaceholder: None = None


@typing.final
class RequestPayload(typing.TypedDict):
    endpoint: Endpoint
    params: typing.Mapping[str, typing.Any]


@typing.final
@dataclass(eq=False, frozen=True)
class MappedValidatorConfig(typing.Generic[_T, ModelT]):
    validator_map: typing.Mapping[_T, typing.Type[ModelT]]
    is_paged: bool
    key_name: str = "key"


class FaceitResourcePath(StrEnum):
    CHAMPIONSHIPS = "championships"
    LEAGUES = "leagues"
    MATCHES = "matches"
    MATCHMAKINGS = "matchmakings"
    PLAYERS = "players"
    RANKINGS = "rankings"
    TEAMS = "teams"


# TODO: Refactor the base resource class if/when support for resources
# other than Data is required, since the current implementation is
# too Data-centric.
@dataclass(eq=False, frozen=True)
class BaseResource(ABC, typing.Generic[ClientT]):
    __slots__ = ("_client", "_raw")

    _client: ClientT
    _raw: bool

    _sync_page_iterator: typing.ClassVar = SyncPageIterator
    _async_page_iterator: typing.ClassVar = AsyncPageIterator
    _timestamp_cfg: typing.ClassVar = TimestampPaginationConfig

    _PARAM_NAME_MAP: typing.ClassVar[typing.Mapping[str, str]] = MappingProxyType({
        "start": "from",
        "category": "type",
    })

    if typing.TYPE_CHECKING:
        PATH: typing.ClassVar[Endpoint]

    def __init_subclass__(
        cls,
        resource_path: typing.Optional[FaceitResourcePath] = None,
        **kwargs: typing.Any,
    ) -> None:
        if hasattr(cls, "PATH"):
            return
        if resource_path is None:
            raise TypeError(
                f"Class {cls.__name__} requires 'path' parameter or a parent with 'PATH' defined."
            )
        cls.PATH = Endpoint(resource_path)
        super().__init_subclass__(**kwargs)

    @property
    def is_raw(self) -> bool:
        return self._raw

    # NOTE: These overloads are necessary as this function directly returns in resource
    # methods, where typing must be strict for public API. Current implementation
    # is sufficient, though alternative typing approaches could be considered.

    @typing.overload
    def _process_response_with_mapped_validator(
        self,
        response: RawAPIPageResponse,
        key: _T,
        config: MappedValidatorConfig[_T, ModelT],
        /,
    ) -> typing.Union[ModelT, RawAPIPageResponse]: ...

    @typing.overload
    def _process_response_with_mapped_validator(
        self,
        response: RawAPIPageResponse,
        key: _T,
        config: MappedValidatorConfig[_T, ModelT],
        /,
    ) -> typing.Union[ItemPage[ModelT], RawAPIPageResponse]: ...

    def _process_response_with_mapped_validator(
        self,
        response: RawAPIPageResponse,
        key: _T,
        config: MappedValidatorConfig[_T, ModelT],
        /,
    ) -> typing.Union[ModelT, ItemPage[ModelT], RawAPIPageResponse]:
        _logger.debug("Processing response with mapped validator for key: %s", key)
        validator = config.validator_map.get(key)
        if validator is None:
            warn(
                f"No model defined for {config.key_name} {key!r}. Consider using the raw response.",
                UserWarning,
                stacklevel=5,
            )
            return response
        # Suppressing type checking warning because we're using a
        # dynamic runtime subscript `ItemPage` is being subscripted
        # with a variable (`validator`) which mypy cannot statically verify
        return self._validate_response(
            response,
            typing.cast("typing.Type[ModelT]", ItemPage[validator])  # type: ignore[valid-type]
            if config.is_paged
            else validator,
        )

    def _validate_response(
        self,
        response: _ResponseT,
        validator: typing.Optional[typing.Type[ModelT]],
        /,
    ) -> typing.Union[_ResponseT, ModelT]:
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
    def _build_params(cls, **params: typing.Any) -> typing.Dict[str, typing.Any]:
        return {
            cls._PARAM_NAME_MAP.get(key, key): value
            for key, value in params.items()
            if value is not None
        }
