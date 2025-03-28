import sys
from typing import TYPE_CHECKING, Literal, TypeVar, Union
from uuid import UUID as _UUID

from pydantic import AnyHttpUrl as _AnyHttpUrl
from pydantic import BaseModel as _PydanticBaseModel

if TYPE_CHECKING:
    from .http import Endpoint as _Endpoint
    from .http.client import BaseAPIClient as _BaseAPIClient
    from .resources import BaseResources as _BaseResources

# At the moment `TypeGuard` is not used in the project,
# but I admit its use in the future, so we leave it imported
if sys.version_info >= (3, 11):
    from typing import Annotated, ParamSpec, Self, TypeAlias, TypeGuard
elif sys.version_info >= (3, 10):
    from typing import Annotated, ParamSpec, TypeAlias, TypeGuard

    from typing_extensions import Self
elif sys.version_info >= (3, 9):
    from typing import Annotated

    from typing_extensions import ParamSpec, Self, TypeAlias, TypeGuard
else:
    from typing_extensions import Annotated, ParamSpec, Self, TypeAlias, TypeGuard

# TODO: Рассмотреть импорт базовых классов из проекта
# в качестве более общего типа данных для асинхронных/синхронных
__all__ = "Annotated", "ParamSpec", "Self", "TypeAlias", "TypeGuard"


EmptyString: TypeAlias = Literal[""]
UrlOrEmpty: TypeAlias = Union[_AnyHttpUrl, EmptyString]
UUIDOrEmpty: TypeAlias = Union[_UUID, EmptyString]
# I reserve the possibility of using this alias in the future
ValidUUID: TypeAlias = Union[_UUID, str, bytes]

EndpointParam: TypeAlias = Union[str, "_Endpoint"]
"""API endpoint to request (`str` or `Endpoint` object)."""

ModelT = TypeVar("ModelT", bound=_PydanticBaseModel)
"""Type variable bound to Pydantic's `BaseModel` for type-safe response handling."""

ClientT = TypeVar("ClientT", bound="_BaseAPIClient")
"""Type variable bound to either `AsyncClient` or `SyncClient` implementations."""

ResourceT = TypeVar("ResourceT", bound="_BaseResources")
"""Type variable bound to either `AsyncResources` or `SyncResources` implementations."""

Raw: TypeAlias = Literal[True]
"""Raw response format."""

Model: TypeAlias = Literal[False]
"""Model response format."""

ResponseFormat = TypeVar("ResponseFormat", bound=Union[Raw, Model])
