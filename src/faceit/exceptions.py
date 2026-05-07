import typing

import httpx


class FaceitError(Exception):
    """Base class for all FACEIT exceptions."""


@typing.final
class DecoupleNotFoundError(FaceitError):
    def __init__(self) -> None:
        super().__init__(
            "The `decouple` package is required but not installed.\n"
            "Install it: pip install decouple\n"
            "Or with faceit[env]"
        )


@typing.final
class MissingAuthTokenError(FaceitError):
    def __init__(self, key: str, /) -> None:
        self.key = key
        super().__init__(
            "Authorization token is missing. "
            f"Please set {key} in your environment file."
        )


class APIError(FaceitError):
    _DEFAULT_MESSAGE: typing.ClassVar = "API request failed"
    _EXPECTED_STATUS_CODE: typing.ClassVar = 0
    _MESSAGE_FORMAT: typing.ClassVar = "[{status_code}] {message}"
    _STATUS_ERRORS: typing.ClassVar[typing.Dict[int, typing.Type["APIError"]]] = {}

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
            self.message = message
        elif response is not None:
            # TODO: Implement proper error parsing to extract the message in a sensible form
            self.message = response.text[:200]
        else:
            self.message = self.__class__._DEFAULT_MESSAGE

        super().__init__(
            self.__class__._MESSAGE_FORMAT.format(
                status_code=self.status_code, message=self.message
            )
        )

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
