import typing

import httpx

from .models.error import ErrorResponse
from .utils import UnsetValue


class FaceitError(Exception):
    pass


@typing.final
class DecoupleMissingError(FaceitError):
    def __init__(self) -> None:
        super().__init__(
            "`python-decouple` is required but not installed.\n"
            "You can install it by running:\n\n"
            "    pip install python-decouple\n\n"
            "Alternatively, you can install it as an extra dependency:\n\n"
            "    pip install faceit[env]\n\n"
            "If you have already installed it, "
            "make sure you're using the correct Python environment."
        )


@typing.final
class MissingAuthTokenError(FaceitError):
    def __init__(self, key: str, /) -> None:
        self.key = key
        msg = f"Authorization token is missing. Please set {key} in your environment file."
        super().__init__(msg)


class APIError(FaceitError):
    _DEFAULT_MESSAGE: typing.ClassVar = "API request failed"
    _EXPECTED_STATUS_CODE: typing.ClassVar[int] = UnsetValue.UNSET
    _MESSAGE_FORMAT: typing.ClassVar = "Status {status_code}: {message}"
    _STATUS_ERRORS: typing.ClassVar[
        typing.Dict[
            int,
            typing.Type["APIError"],
        ]
    ] = {}

    def __init_subclass__(
        cls,
        code: httpx.codes,
        default_message: typing.Optional[str] = None,
        **kwargs: typing.Any,
    ) -> None:
        cls._EXPECTED_STATUS_CODE = code.value
        cls._DEFAULT_MESSAGE = default_message or code.get_reason_phrase(code.value)
        cls._STATUS_ERRORS[code.value] = cls
        super().__init_subclass__(**kwargs)

    def __init__(
        self,
        response: typing.Optional[httpx.Response] = None,
        /,
        *,
        message: typing.Optional[str] = None,
    ) -> None:
        self.response = response
        self.status_code = (
            self.__class__._EXPECTED_STATUS_CODE
            if response is None
            else response.status_code
        )
        if message is not None:
            # If a custom message is provided (e.g., "Invalid JSON"),
            # there's no need to parse `response.json()`
            self.validated_response = ErrorResponse()
            self.error_detail = message
        elif response is not None:
            self.validated_response = ErrorResponse.parse_safe(response.json())
            error_messages = [e.message for e in self.validated_response.errors]
            self.error_detail = (
                " ".join(error_messages)
                if error_messages
                else self.__class__._DEFAULT_MESSAGE
            )
        else:
            self.validated_response = ErrorResponse()
            self.error_detail = self.__class__._DEFAULT_MESSAGE
        self.message = self.__class__._MESSAGE_FORMAT.format(
            status_code=self.status_code, message=self.error_detail
        )
        super().__init__(self.message)

    @classmethod
    def from_response(cls, response: httpx.Response, /) -> "APIError":
        return cls._STATUS_ERRORS.get(response.status_code, APIError)(response)


# fmt: off
@typing.final
class BadRequestError(APIError, code=httpx.codes.BAD_REQUEST): ...
@typing.final
class UnauthorizedError(APIError, code=httpx.codes.UNAUTHORIZED): ...
@typing.final
class ForbiddenError(APIError, code=httpx.codes.FORBIDDEN): ...
@typing.final
class NotFoundError(APIError, code=httpx.codes.NOT_FOUND): ...
@typing.final
class TooManyRequestsError(APIError, code=httpx.codes.TOO_MANY_REQUESTS): ...
@typing.final
class InternalServerError(APIError, code=httpx.codes.INTERNAL_SERVER_ERROR): ...
@typing.final
class ServiceUnavailableError(APIError, code=httpx.codes.SERVICE_UNAVAILABLE): ...
# fmt: on
