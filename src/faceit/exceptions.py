# TODO: Enhance this module by handling additional
# exceptions and improving its overall design.


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


class APIError(FaceitError):  # TODO: Make this better
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Status {status_code}: {message}")
        self.status_code = status_code
        self.message = message
