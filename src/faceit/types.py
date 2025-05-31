import typing
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field
from typing_extensions import NotRequired, ParamSpec, TypeAlias

if typing.TYPE_CHECKING:
    from .http import Endpoint
    from .http.client import BaseAPIClient
    from .resources import AsyncDataResource, SyncDataResource
    from .resources.base import BaseResource

_T = typing.TypeVar("_T")
_R = typing.TypeVar("_R")
_T_co = typing.TypeVar("_T_co", covariant=True)
_P = ParamSpec("_P")

ModelT = typing.TypeVar("ModelT", bound="BaseModel")
ClientT = typing.TypeVar("ClientT", bound="BaseAPIClient[typing.Any]")
DataResourceT = typing.TypeVar(
    "DataResourceT", bound=typing.Union["SyncDataResource", "AsyncDataResource"]
)

APIResponseFormatT = typing.TypeVar("APIResponseFormatT", "Raw", "Model")
PaginationMethodT = typing.TypeVar("PaginationMethodT", bound="BaseMethodProtocol")

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


class BaseMethodProtocol(typing.Protocol):
    __name__: str
    __self__: "BaseResource[typing.Any]"
    __call__: typing.Callable[..., typing.Any]


class BasePaginationMethod(BaseMethodProtocol, typing.Protocol[_T_co]):
    def __call__(
        self,
        *args: typing.Any,
        offset: int = Field(...),
        limit: int = Field(...),
        **kwargs: typing.Any,
    ) -> _T_co: ...


class SyncPaginationMethod(BasePaginationMethod[_T_co], typing.Protocol): ...


class AsyncPaginationMethod(
    BasePaginationMethod[typing.Awaitable[_T_co]], typing.Protocol
): ...


class BaseUnixPaginationMethod(BaseMethodProtocol, typing.Protocol[_T_co]):
    def __call__(
        self,
        *args: typing.Any,
        offset: int = Field(...),
        limit: int = Field(...),
        start: typing.Optional[int] = None,
        to: typing.Optional[int] = None,
        **kwargs: typing.Any,
    ) -> _T_co: ...


class SyncUnixPaginationMethod(BaseUnixPaginationMethod[_T_co], typing.Protocol): ...


class AsyncUnixPaginationMethod(
    BaseUnixPaginationMethod[typing.Awaitable[_T_co]], typing.Protocol
): ...
