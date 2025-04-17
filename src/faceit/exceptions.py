# TODO: больше исключений, в принципе реализовать данный модуль лучше


class FaceitError(Exception):
    pass


class APIError(FaceitError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Status {status_code}: {message}")
        self.status_code = status_code
        self.message = message
