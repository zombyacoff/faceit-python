import typing

from pydantic import BaseModel, ValidationError
from typing_extensions import Self


class ErrorDetail(BaseModel):
    message: str
    code: str
    http_status: int
    parameters: typing.List[typing.Any]


class ErrorResponse(BaseModel):
    errors: typing.List[ErrorDetail] = []

    @classmethod
    def parse_safe(cls, data: typing.Any, /) -> Self:
        try:
            return cls.model_validate(data)
        except ValidationError:
            return cls()
