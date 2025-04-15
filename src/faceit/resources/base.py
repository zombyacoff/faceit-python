import logging
import typing as t
from abc import ABC
from enum import auto

from pydantic import ValidationError
from strenum import LowercaseStrEnum

from faceit import _repr
from faceit._typing import ClientT, ModelT, RawAPIResponse
from faceit.http import Endpoint

from .pagination import (
    AsyncPageIterator,
    SyncPageIterator,
    TimestampPaginationConfig,
)

_logger = logging.getLogger(__name__)

_ResponseT = t.TypeVar("_ResponseT", bound=RawAPIResponse)


@t.final
class FaceitResourcePath(LowercaseStrEnum):
    PLAYERS = auto()
    CHAMPIONSHIPS = auto()


@t.final
class RequestPayload(t.TypedDict):
    endpoint: Endpoint
    params: t.Dict[str, t.Any]


@_repr.representation("path", "raw")
class BaseResource(t.Generic[ClientT], ABC):
    _resource_path: t.ClassVar[FaceitResourcePath]

    _sync_page_iterator: t.ClassVar = SyncPageIterator
    _async_page_iterator: t.ClassVar = AsyncPageIterator
    _timestamp_cfg: t.ClassVar = TimestampPaginationConfig

    def __init__(self, client: ClientT, /, *, raw: bool) -> None:
        self._client = client
        self._raw = raw
        self._path = Endpoint(self.__class__._resource_path)

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "_resource_path"):
            raise NotImplementedError(
                f"Class {cls.__name__} must define "
                f"class attribute '_resource_path'"
            )

    @property
    def path(self) -> Endpoint:
        return self._path

    @property
    def raw(self) -> bool:
        return self._raw

    def _validate_response(
        self, response: _ResponseT, validator: t.Optional[t.Type[ModelT]], /
    ) -> t.Union[_ResponseT, ModelT]:
        if validator is not None and not self.raw:
            try:
                return validator.model_validate(response)
            except ValidationError:
                _logger.exception(
                    "Response validation failed for %s model",
                    validator.__name__,
                )
        return response

    @staticmethod
    def _build_params(**params: t.Any) -> t.Dict[str, t.Any]:
        return {
            ("from" if key == "start" else key): value
            for key, value in params.items()
            if value is not None
        }
