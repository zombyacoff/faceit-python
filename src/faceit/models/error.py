import typing

from pydantic import BaseModel, ValidationError
from typing_extensions import Self


@typing.final
class ErrorDetail(BaseModel):
    message: str
    code: str
    http_status: int
    parameters: typing.List[typing.Any]


@typing.final
class ErrorResponse(BaseModel):
    errors: typing.List[ErrorDetail] = []

    @classmethod
    def parse_safe(cls, data: typing.Dict[str, typing.Any], /) -> Self:
        try:
            return cls.model_validate(data)
        except ValidationError:
            return cls()
