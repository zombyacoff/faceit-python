import sys
import typing as t
from uuid import UUID as _UUID

from pydantic import AnyHttpUrl as _AnyHttpUrl
from pydantic import BaseModel as _PydanticBaseModel

if t.TYPE_CHECKING:
    from .http import Endpoint as _Endpoint
    from .http._client import BaseAPIClient as _BaseAPIClient
    from .resources import BaseResources as _BaseResources

# At the moment `TypeGuard` is not used in the project,
# but I admit its use in the future, so we leave it imported
if sys.version_info >= (3, 11):
    from typing import (
        Annotated,
        NotRequired,
        ParamSpec,
        Required,
        Self,
        TypeAlias,
        TypeGuard,
    )
elif sys.version_info >= (3, 10):
    from typing import Annotated, ParamSpec, TypeAlias, TypeGuard

    from typing_extensions import NotRequired, Required, Self
elif sys.version_info >= (3, 9):
    from typing import Annotated

    from typing_extensions import (
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
        NotRequired,
        ParamSpec,
        Required,
        Self,
        TypeAlias,
        TypeGuard,
    )

__all__ = (
    "Annotated",
    "NotRequired",
    "ParamSpec",
    "Required",
    "Self",
    "TypeAlias",
    "TypeGuard",
)

EmptyString: TypeAlias = t.Literal[""]
UrlOrEmpty: TypeAlias = t.Union[_AnyHttpUrl, EmptyString]
UUIDOrEmpty: TypeAlias = t.Union[_UUID, EmptyString]

EndpointParam: TypeAlias = t.Union[str, "_Endpoint"]

ModelT = t.TypeVar("ModelT", bound=_PydanticBaseModel)
ClientT = t.TypeVar("ClientT", bound="_BaseAPIClient")
ResourceT = t.TypeVar("ResourceT", bound="_BaseResources")

Raw: TypeAlias = t.Literal[True]
Model: TypeAlias = t.Literal[False]
APIResponseFormat = t.TypeVar("APIResponseFormat", bound=t.Union[Raw, Model])

RawAPIItem: TypeAlias = t.Dict[str, t.Any]
RawAPIPageResponse = t.TypedDict(
    "RawAPIPageResponse",
    {
        "items": t.List[RawAPIItem],
        # Required pagination parameters
        "start": int,
        "end": int,
        # Unix timestamps (in milliseconds), optional
        "from": NotRequired[int],
        "to": NotRequired[int],
    },
)
APIResponse: TypeAlias = t.Union[RawAPIItem, RawAPIPageResponse]
