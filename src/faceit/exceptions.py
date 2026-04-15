import typing

import httpx


class FaceitError(Exception):
    pass


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


class MissingAuthTokenError(FaceitError):
    def __init__(self, key: str, /) -> None:
        super().__init__(
            "Authorization token is missing. "
            f"Please set {key} in your environment file."
        )
        self.key = key


class APIError(FaceitError):
    _STATUS_ERRORS: typing.ClassVar[
        typing.Dict[
            int,
            typing.Type["APIError"],
        ]
    ] = {}
    _MESSAGE_FORMAT: typing.ClassVar = "Status {status_code}: {message}"

    _expected_status_code: typing.ClassVar = 0
    _default_message: typing.ClassVar = "API request failed"

    def __init_subclass__(
        cls,
        code: httpx.codes,
        default_message: typing.Optional[str] = None,
        **kwargs: typing.Any,
    ) -> None:
        cls._expected_status_code = code.value
        cls._default_message = default_message or code.get_reason_phrase(code.value)
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
            self.__class__._expected_status_code
            if response is None
            else response.status_code
        )
        self.message = message or (
            self.__class__._MESSAGE_FORMAT.format(
                status_code=self.status_code,
                message=self.__class__._default_message,
            )
            if self.response is None
            else self.__class__._MESSAGE_FORMAT.format(
                status_code=self.status_code,
                message=self.response.text,
            )
        )
        super().__init__(self.message)

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
