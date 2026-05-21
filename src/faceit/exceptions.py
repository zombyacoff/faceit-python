from typing import Any, ClassVar, final

import httpx


class FaceitError(Exception):
    """Base class for all FACEIT exceptions."""


@final
class DecoupleNotFoundError(FaceitError):
    def __init__(self) -> None:
        super().__init__(
            "The `decouple` package is required but not installed.\n"
            "Install it: pip install decouple\n"
            "Or with faceit[env]"
        )


@final
class MissingAuthTokenError(FaceitError):
    def __init__(self, key: str, /) -> None:
        self.key = key
        super().__init__(
            "Authorization token is missing. "
            f"Please set {key} in your environment file."
        )


class APIError(FaceitError):
    _DEFAULT_MESSAGE: ClassVar = "API request failed"
    _EXPECTED_STATUS_CODE: ClassVar = 0
    _MESSAGE_FORMAT: ClassVar = "[{status_code}] {message}"
    _STATUS_ERRORS: ClassVar[dict[int, type["APIError"]]] = {}

    def __init_subclass__(
        cls,
        code: httpx.codes,
        default_message: str | None = None,
        **kwargs: Any,
    ) -> None:
        cls._EXPECTED_STATUS_CODE = code.value
        cls._DEFAULT_MESSAGE = default_message or code.get_reason_phrase(code.value)
        cls._STATUS_ERRORS[code.value] = cls
        super().__init_subclass__(**kwargs)

    def __init__(
        self,
        response: httpx.Response | None = None,
        /,
        *,
        message: str | None = None,
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
class BadRequestError(APIError, code=httpx.codes.BAD_REQUEST): ...
class UnauthorizedError(APIError, code=httpx.codes.UNAUTHORIZED): ...
class ForbiddenError(APIError, code=httpx.codes.FORBIDDEN): ...
class NotFoundError(APIError, code=httpx.codes.NOT_FOUND): ...
class TooManyRequestsError(APIError, code=httpx.codes.TOO_MANY_REQUESTS): ...
class InternalServerError(APIError, code=httpx.codes.INTERNAL_SERVER_ERROR): ...
class ServiceUnavailableError(APIError, code=httpx.codes.SERVICE_UNAVAILABLE): ...
# fmt: on
