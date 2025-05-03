import typing as t
from uuid import UUID

import typing_extensions as te
from pydantic import AnyHttpUrl, BaseModel, Field

if t.TYPE_CHECKING:
    from .http import Endpoint
    from .http.client import BaseAPIClient
    from .resources import AsyncDataResource, SyncDataResource
    from .resources.base import BaseResource

_T = t.TypeVar("_T")
_R = t.TypeVar("_R")
_T_co = t.TypeVar("_T_co", covariant=True)

ModelT = t.TypeVar("ModelT", bound=BaseModel)
ClientT = t.TypeVar("ClientT", bound="BaseAPIClient")
DataResourceT = t.TypeVar(
    "DataResourceT", bound=t.Union["SyncDataResource", "AsyncDataResource"]
)

APIResponseFormatT = t.TypeVar("APIResponseFormatT", "Raw", "Model")
PaginationMethodT = t.TypeVar("PaginationMethodT", bound="BaseMethodProtocol")

EmptyString: te.TypeAlias = t.Literal[""]
UrlOrEmpty: te.TypeAlias = t.Union[AnyHttpUrl, EmptyString]
UUIDOrEmpty: te.TypeAlias = t.Union[UUID, EmptyString]
EndpointParam: te.TypeAlias = t.Union[str, "Endpoint"]
ValidUUID: te.TypeAlias = t.Union[UUID, str, bytes]

Raw = t.NewType("Raw", bool)
Model = t.NewType("Model", bool)

# Placeholder type that signals developers to implement a proper model
# for a resource method. Acts as a temporary stub during development.
ModelNotImplemented: te.TypeAlias = BaseModel

RawAPIItem = t.NewType("RawAPIItem", t.Dict[str, t.Any])
RawAPIPageResponse = t.TypedDict(
    "RawAPIPageResponse",
    {
        "items": t.List[RawAPIItem],
        # Required pagination parameters (cursor based)
        "start": int,
        "end": int,
        # Unix timestamps (in milliseconds)
        "from": te.NotRequired[int],
        "to": te.NotRequired[int],
    },
)
RawAPIResponse: te.TypeAlias = t.Union[RawAPIItem, RawAPIPageResponse]


class BaseMethodProtocol(t.Protocol):
    __name__: str
    __self__: "BaseResource"
    __call__: t.Callable[..., t.Any]


class BasePaginationMethod(BaseMethodProtocol, t.Protocol[_T_co]):
    def __call__(
        self,
        *args: t.Any,
        offset: int = Field(...),
        limit: int = Field(...),
        **kwargs: t.Any,
    ) -> _T_co: ...


class SyncPaginationMethod(BasePaginationMethod[_T_co], t.Protocol): ...


class AsyncPaginationMethod(
    BasePaginationMethod[t.Awaitable[_T_co]], t.Protocol
): ...


class BaseUnixPaginationMethod(BaseMethodProtocol, t.Protocol[_T_co]):
    def __call__(
        self,
        *args: t.Any,
        offset: int = Field(...),
        limit: int = Field(...),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
        **kwargs: t.Any,
    ) -> _T_co: ...


class SyncUnixPaginationMethod(
    BaseUnixPaginationMethod[_T_co], t.Protocol
): ...


class AsyncUnixPaginationMethod(
    BaseUnixPaginationMethod[t.Awaitable[_T_co]], t.Protocol
): ...
