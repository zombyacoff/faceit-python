import typing

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    message: str
    code: str
    http_status: int
    parameters: typing.List[typing.Any]


class ErrorResponse(BaseModel):
    errors: typing.List[ErrorDetail] = []
