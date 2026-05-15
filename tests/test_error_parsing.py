import httpx

from faceit.exceptions import APIError, NotFoundError


def test_api_error_parsing_with_errors_list() -> None:
    error = APIError.from_response(
        httpx.Response(
            status_code=404,
            content=b'{"errors":[{"message":"The resource was not found.","code":"err_nf0"}]}',
            request=httpx.Request("GET", "https://example.com"),
        )
    )
    assert isinstance(error, NotFoundError)
    assert error.message == "The resource was not found."
    assert str(error) == "[404] The resource was not found."


def test_api_error_parsing_without_errors_list() -> None:
    error = APIError.from_response(
        httpx.Response(
            status_code=400,
            content=b'{"message":"Bad request"}',
            request=httpx.Request("GET", "https://example.com"),
        )
    )
    assert error.message == '{"message":"Bad request"}'


def test_api_error_parsing_invalid_json() -> None:
    error = APIError.from_response(
        httpx.Response(
            status_code=500,
            content=b"Internal Server Error",
            request=httpx.Request("GET", "https://example.com"),
        )
    )
    assert error.message == "Internal Server Error"


def test_api_error_parsing_empty_errors() -> None:
    error = APIError.from_response(
        httpx.Response(
            status_code=404,
            content=b'{"errors":[]}',
            request=httpx.Request("GET", "https://example.com"),
        )
    )
    assert error.message == '{"errors":[]}'
