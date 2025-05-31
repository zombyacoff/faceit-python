# TODO: Enhance this module by handling additional
# exceptions and improving its overall design.


class FaceitError(Exception):
    """Base exception for all Faceit-related errors."""


class MissingAuthTokenError(FaceitError):
    """
    Raised when the required authorization token is missing from the
    environment or configuration files.
    """


class APIError(FaceitError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Status {status_code}: {message}")
        self.status_code = status_code
        self.message = message
