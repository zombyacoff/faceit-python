import logging
from abc import ABC
from enum import auto
from typing import Any, ClassVar, Dict, Generic, Optional, Type, Union, final

from pydantic import ValidationError
from strenum import LowercaseStrEnum

from faceit.http import Endpoint
from faceit.types import ClientT, EndpointParam, ModelT

_logger = logging.getLogger(__name__)


@final
class FaceitResourcePath(LowercaseStrEnum):
    """FACEIT API endpoint paths for resource mapping."""

    PLAYERS = auto()
    # MATCHES = "matches"
    # TOURNAMENTS = "tournaments"
    CHAMPIONSHIPS = auto()
    # HUBS = "hubs"
    # GAMES = "games"
    # LEADERBOARDS = "leaderboards"
    # TEAMS = "teams"


class BaseResource(Generic[ClientT], ABC):
    _resource_path: ClassVar[FaceitResourcePath]

    def __init__(self, client: ClientT, *, raw: bool = False) -> None:
        self._client = client
        self._raw = raw
        self._path = Endpoint(self.__class__._resource_path)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "_resource_path"):
            raise TypeError(f"Class {cls.__name__} must define class attribute '_resource_path'")

    @property
    def raw(self) -> bool:
        return self._raw

    @property
    def path(self) -> Endpoint:
        return self._path

    def __str__(self) -> str:
        return f"{self.__class__.__name__} {"raw" if self.raw else "validated"} resource at '{self.path}' endpoint"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path!r}, raw={self.raw})"

    @staticmethod
    def _build_params(**params: Any) -> Dict[str, Any]:
        """Build a dictionary of parameters for API requests.

        This method performs two important transformations:
        1. Converts the `start` parameter to `from` for API compatibility
           (since `from` is a reserved keyword in Python)
        2. Filters out None values to prevent sending empty parameters
        """
        return {("from" if key == "start" else key): value for key, value in params.items() if value is not None}

    @staticmethod
    def _build_request_payload(endpoint: EndpointParam, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build a request payload with the specified endpoint and parameters."""
        return {"endpoint": endpoint, "params": params}

    def _validate_response(
        self, response: Dict[str, Any], validator: Optional[Type[ModelT]]
    ) -> Union[Dict[str, Any], ModelT]:
        """Validate API response using the provided validator model.

        Returns raw response if `self.raw=True` or `validator=None`.
        Falls back to raw response on validation errors (with logging).
        """
        if self.raw or validator is None:
            return response
        try:
            return validator.model_validate(response)
        except ValidationError as e:
            _logger.error("Error validating response: %s", e)
            return response
