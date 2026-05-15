from collections.abc import Awaitable, Callable
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    NewType,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypedDict,
    TypeVar,
)
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel
from typing_extensions import NotRequired

from .constants import GameID, Region

if TYPE_CHECKING:
    from .api import AsyncDataResource, SyncDataResource
    from .http import Endpoint
    from .http.client import BaseAPIClient
    from .models.custom_types import TimestampMs

_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_R = TypeVar("_R")
_P = ParamSpec("_P")

ModelT = TypeVar("ModelT", bound="BaseModel")
ClientT = TypeVar("ClientT", bound="BaseAPIClient[Any, Any]")
DataResourceT = TypeVar("DataResourceT", bound="SyncDataResource | AsyncDataResource")

APIResponseFormatT = TypeVar("APIResponseFormatT", "Raw", "Model")
PaginationMethodT = TypeVar(
    "PaginationMethodT", bound="BaseResourceMethodProtocol[Any]"
)

EmptyString: TypeAlias = Literal[""]
UrlOrEmpty: TypeAlias = AnyHttpUrl | EmptyString
UUIDOrEmpty: TypeAlias = UUID | EmptyString
EndpointParam: TypeAlias = "str | Endpoint"
ValidUUID: TypeAlias = UUID | str | bytes

AnyCSID: TypeAlias = Literal[GameID.CS2, GameID.CSGO]

Raw = NewType("Raw", bool)
Model = NewType("Model", bool)

# Placeholder type that signals developers to implement a proper model
# for a resource method. Acts as a temporary stub during development.
ModelNotImplemented: TypeAlias = BaseModel

RegionIdentifier: TypeAlias = Region | str

RawAPIItem: TypeAlias = dict[str, Any]
RawAPIPageResponse = TypedDict(
    "RawAPIPageResponse",
    {
        "items": list[RawAPIItem],
        # Required pagination parameters (cursor based)
        "start": int,
        "end": int,
        # Unix timestamps (in milliseconds)
        "from": NotRequired["TimestampMs"],
        "to": NotRequired["TimestampMs"],
    },
)
RawAPIResponse: TypeAlias = RawAPIItem | RawAPIPageResponse


class BaseResourceMethodProtocol(Protocol[_T]):
    __name__: str
    __call__: Callable[..., _T]


class SyncResourceMethodProtocol(
    BaseResourceMethodProtocol[_T],
    Protocol,
): ...


class AsyncResourceMethodProtocol(
    BaseResourceMethodProtocol[Awaitable[_T]],
    Protocol,
): ...
