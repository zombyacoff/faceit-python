import typing

import httpx
from pydantic import ValidationError

from .models.error import ErrorResponse
from .utils import UnsetValue


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
        self.validated_response = self.__class__._validate_response(response)
        self.status_code = (
            self.__class__._EXPECTED_STATUS_CODE
            if response is None
            else response.status_code
        )
        self.error_detail = self._compute_error_detail()
        self.message = message or self.__class__._MESSAGE_FORMAT.format(
            status_code=self.status_code, message=self.error_detail
        )
        super().__init__(self.message)

    def _compute_error_detail(self) -> str:
        if self.response is None:
            return self.__class__._DEFAULT_MESSAGE
        messages = [e.message for e in self.validated_response.errors]
        return " ".join(messages) if messages else self.__class__._DEFAULT_MESSAGE

    @classmethod
    def from_response(cls, response: httpx.Response, /) -> "APIError":
        return cls._STATUS_ERRORS.get(response.status_code, APIError)(response)

    @staticmethod
    def _validate_response(
        response: typing.Optional[httpx.Response], /
    ) -> ErrorResponse:
        if response is None:
            return ErrorResponse()
        try:
            # NOTE: Currently, we assume the FACEIT API strictly adheres to the `ErrorResponse` model.
            # If we encounter cases where the API returns an unexpected format,
            # we will promptly update this validation. Keeping it as is for now.
            return ErrorResponse.model_validate(response.json())
        except (ValidationError, AttributeError, ValueError):
            return ErrorResponse()


# fmt: off
class BadRequestError(APIError, code=httpx.codes.BAD_REQUEST): ...
class UnauthorizedError(APIError, code=httpx.codes.UNAUTHORIZED): ...
class ForbiddenError(APIError, code=httpx.codes.FORBIDDEN): ...
class NotFoundError(APIError, code=httpx.codes.NOT_FOUND): ...
class TooManyRequestsError(APIError, code=httpx.codes.TOO_MANY_REQUESTS): ...
class InternalServerError(APIError, code=httpx.codes.INTERNAL_SERVER_ERROR): ...
class ServiceUnavailableError(APIError, code=httpx.codes.SERVICE_UNAVAILABLE): ...
# fmt: on
