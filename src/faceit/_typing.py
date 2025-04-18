import sys
import typing as t
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field

if sys.version_info >= (3, 13):
    from typing import (
        Annotated,
        Doc,
        NotRequired,
        ParamSpec,
        Required,
        Self,
        TypeAlias,
        TypeGuard,
    )
elif sys.version_info >= (3, 11):
    from typing import (
        Annotated,
        NotRequired,
        ParamSpec,
        Required,
        Self,
        TypeAlias,
        TypeGuard,
    )

    from typing_extensions import Doc
elif sys.version_info >= (3, 10):
    from typing import Annotated, ParamSpec, TypeAlias, TypeGuard

    from typing_extensions import Doc, NotRequired, Required, Self
elif sys.version_info >= (3, 9):
    from typing import Annotated

    from typing_extensions import (
        Doc,
        NotRequired,
        ParamSpec,
        Required,
        Self,
        TypeAlias,
        TypeGuard,
    )
else:
    from typing_extensions import (
        Annotated,
        Doc,
        NotRequired,
        ParamSpec,
        Required,
        Self,
        TypeAlias,
        TypeGuard,
    )

if t.TYPE_CHECKING:
    from ._resources import BaseResources
    from .http import Endpoint
    from .http._client import BaseAPIClient

__all__ = (
    "Annotated",
    # Will transition to this documentation style when VSCode and other IDEs
    # provide proper support for PEP 727 Doc annotations
    "Doc",
    "NotRequired",
    "ParamSpec",
    "Required",
    "Self",
    "TypeAlias",
    # At the moment `TypeGuard` is not used in the project,
    # but I admit its use in the future, so we leave it imported
    "TypeGuard",
)

_T_co = t.TypeVar("_T_co", covariant=True)

ModelT = t.TypeVar("ModelT", bound=BaseModel)
ClientT = t.TypeVar("ClientT", bound="BaseAPIClient")
ResourceT = t.TypeVar("ResourceT", bound="BaseResources")

APIResponseFormatT = t.TypeVar("APIResponseFormatT", "Raw", "Model")
PaginationMethodT = t.TypeVar("PaginationMethodT", bound="BaseMethodProtocol")

EmptyString: TypeAlias = t.Literal[""]
UrlOrEmpty: TypeAlias = t.Union[AnyHttpUrl, EmptyString]
UUIDOrEmpty: TypeAlias = t.Union[UUID, EmptyString]
EndpointParam: TypeAlias = t.Union[str, "Endpoint"]
ValidUUID: TypeAlias = t.Union[UUID, str, bytes]

Raw: TypeAlias = t.Literal[True]
Model: TypeAlias = t.Literal[False]

# Placeholder type that signals developers to implement a proper model
# for a resource method. Acts as a temporary stub during development.
ModelNotImplemented: TypeAlias = BaseModel

RawAPIItem = t.NewType("RawAPIItem", t.Dict[str, t.Any])
RawAPIPageResponse = t.TypedDict(
    "RawAPIPageResponse",
    {
        "items": t.List[RawAPIItem],
        # Required pagination parameters (cursor based)
        "start": int,
        "end": int,
        # Unix timestamps (in milliseconds)
        "from": NotRequired[int],
        "to": NotRequired[int],
    },
)
RawAPIResponse: TypeAlias = t.Union[RawAPIItem, RawAPIPageResponse]


class BaseMethodProtocol(t.Protocol):
    __name__: str
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
