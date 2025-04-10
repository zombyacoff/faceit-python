import logging
import typing as t
from abc import ABC
from enum import auto

from pydantic import ValidationError
from strenum import LowercaseStrEnum

from faceit._types import APIResponse, ClientT, EndpointParam, ModelT
from faceit.http import Endpoint

from .pagination import AsyncPageIterator, SyncPageIterator

_logger = logging.getLogger(__name__)

_ResponseT = t.TypeVar("_ResponseT", bound=APIResponse)


@t.final
class FaceitResourcePath(LowercaseStrEnum):
    PLAYERS = auto()
    CHAMPIONSHIPS = auto()


class BaseResource(t.Generic[ClientT], ABC):
    _resource_path: t.ClassVar[FaceitResourcePath]

    _sync_page_iterator: t.ClassVar = SyncPageIterator
    _async_page_iterator: t.ClassVar = AsyncPageIterator

    _unix_cfg = t.ClassVar = SyncPageIterator.UNIX_CFG

    def __init__(self, client: ClientT, *, raw: bool = False) -> None:
        self._client = client
        self._raw = raw
        self._path = Endpoint(self.__class__._resource_path)

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "_resource_path"):
            raise NotImplementedError(
                f"Class {cls.__name__} must define class attribute '_resource_path'"
            )

    @property
    def raw(self) -> bool:
        return self._raw

    @property
    def path(self) -> Endpoint:
        return self._path

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__} "
            f"{"raw" if self.raw else "validated"} resource at '{self.path}' endpoint"
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path!r}, raw={self.raw})"

    @staticmethod
    def _build_params(**params: t.Any) -> t.Dict[str, t.Any]:
        return {
            ("from" if key == "start" else key): value
            for key, value in params.items()
            if value is not None
        }

    @staticmethod
    def _build_request_payload(
        endpoint: EndpointParam, params: t.Dict[str, t.Any]
    ) -> t.Dict[str, t.Any]:
        return {"endpoint": endpoint, "params": params}

    def _validate_response(
        self, response: _ResponseT, validator: t.Optional[t.Type[ModelT]]
    ) -> t.Union[_ResponseT, ModelT]:
        if self.raw or validator is None:
            return response
        try:
            return validator.model_validate(response)
        except ValidationError:
            _logger.exception("Error validating response")
            return response
