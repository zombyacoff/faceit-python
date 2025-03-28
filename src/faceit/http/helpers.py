from typing import Optional, final

from faceit.types import EndpointParam, Self


@final
class Endpoint:
    """Represents a URL endpoint for API requests.

    This class provides a convenient way to build and manipulate URL paths
    for API endpoints. It supports path composition through the division
    operator (/) and explicit methods.

    Attributes:
        path_parts: List of path segments that make up the endpoint.
        base_path: Optional base URL or path prefix.

    Examples:
        ```
        base = Endpoint("api", "v1", base_path="https://example.com")
        assert str(base / "users") == "https://example.com/api/v1/users"
        ```
    """

    __slots__ = "base_path", "path_parts"

    def __init__(self, *path_parts: str, base_path: Optional[str] = None) -> None:
        self.path_parts = list(filter(None, path_parts))
        self.base_path = base_path

    def __str__(self) -> str:
        all_parts = ([self.base_path] if self.base_path else []) + self.path_parts
        return "/".join(part.strip("/") for part in all_parts if part)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self)!r})"

    def __truediv__(self, other: EndpointParam) -> Self:
        if isinstance(other, str):
            return self.add(other)
        if isinstance(other, self.__class__):
            return self.__class__(*self.path_parts, *other.path_parts, base_path=self.base_path)
        raise TypeError(f"unsupported operand type(s) for /: '{self.__class__.__name__}' and '{type(other).__name__}'")

    def add(self, *path_parts: str) -> Self:
        return self.__class__(*self.path_parts, *path_parts, base_path=self.base_path)

    def with_base(self, base_path: str) -> Self:
        return self.__class__(*self.path_parts, base_path=base_path)
