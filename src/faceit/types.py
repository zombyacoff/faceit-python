import typing
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field
from typing_extensions import NotRequired, ParamSpec, TypeAlias

from .constants import Region

if typing.TYPE_CHECKING:
    from .http import Endpoint
    from .http.client import BaseAPIClient
    from .resources import AsyncDataResource, SyncDataResource

_T = typing.TypeVar("_T")
_R = typing.TypeVar("_R")
_P = ParamSpec("_P")

ModelT = typing.TypeVar("ModelT", bound="BaseModel")
ClientT = typing.TypeVar("ClientT", bound="BaseAPIClient[typing.Any, typing.Any]")
DataResourceT = typing.TypeVar(
    "DataResourceT", bound=typing.Union["SyncDataResource", "AsyncDataResource"]
)

APIResponseFormatT = typing.TypeVar("APIResponseFormatT", "Raw", "Model")
PaginationMethodT = typing.TypeVar(
    "PaginationMethodT", bound="BaseResourceMethodProtocol[typing.Any]"
)

EmptyString: TypeAlias = typing.Literal[""]
UrlOrEmpty: TypeAlias = typing.Union[AnyHttpUrl, EmptyString]
UUIDOrEmpty: TypeAlias = typing.Union[UUID, EmptyString]
EndpointParam: TypeAlias = typing.Union[str, "Endpoint"]
ValidUUID: TypeAlias = typing.Union[UUID, str, bytes]

Raw = typing.NewType("Raw", bool)
Model = typing.NewType("Model", bool)

# Placeholder type that signals developers to implement a proper model
# for a resource method. Acts as a temporary stub during development.
ModelNotImplemented: TypeAlias = BaseModel

RegionIdentifier: TypeAlias = typing.Union[Region, str]

RawAPIItem = typing.NewType("RawAPIItem", typing.Dict[str, typing.Any])
RawAPIPageResponse = typing.TypedDict(
    "RawAPIPageResponse",
    {
        "items": typing.List[RawAPIItem],
        # Required pagination parameters (cursor based)
        "start": int,
        "end": int,
        # Unix timestamps (in milliseconds)
        "from": NotRequired[int],
        "to": NotRequired[int],
    },
)
RawAPIResponse: TypeAlias = typing.Union[RawAPIItem, RawAPIPageResponse]


class BaseResourceMethodProtocol(typing.Protocol[_T]):
    __name__: str
    __call__: typing.Callable[..., _T]


class SyncResourceMethodProtocol(BaseResourceMethodProtocol[_T], typing.Protocol): ...


class AsyncResourceMethodProtocol(
    BaseResourceMethodProtocol[typing.Awaitable[_T]], typing.Protocol
): ...
