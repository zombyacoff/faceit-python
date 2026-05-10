import asyncio
import ssl
import typing
from time import time
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
import tenacity

from faceit.constants import BASE_WIKI_URL
from faceit.exceptions import APIError, BadRequestError
from faceit.http import AsyncClient, Endpoint, SupportedMethod, SyncClient
from faceit.http.client import (
    BaseAPIClient,
    _BaseAsyncClient,
    _BaseSyncClient,
    is_ssl_error,
)


def _create_response_mock(
    status_code: int = 200,
    json_data: typing.Optional[typing.Dict[str, typing.Any]] = None,
    text: str = "",
    raise_for_status: typing.Optional[Exception] = None,
) -> Mock:
    if json_data is None:
        json_data = {"data": "test_data"}

    response = Mock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.url = "https://test.com/api"
    response.text = text or str(json_data)

    if raise_for_status:
        response.raise_for_status.side_effect = raise_for_status
    else:
        response.raise_for_status.return_value = None

    return response


def _create_error_response(status_code: int = 400) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.json.return_value = {"errors": []}
    response.url = "https://test.com/api"
    response.text = httpx.codes.get_reason_phrase(status_code)
    response.is_server_error = status_code >= 500

    error = httpx.HTTPStatusError(
        response.text,
        request=Mock(),
        response=response,
    )
    response.raise_for_status.side_effect = error

    return response


@pytest.fixture(scope="module")
def mock_response() -> Mock:
    return _create_response_mock()


@pytest.fixture(scope="module")
def error_response() -> Mock:
    return _create_error_response(400)


@pytest.fixture(scope="module")
def server_error_response() -> Mock:
    return _create_error_response(500)


@pytest.fixture(scope="module")
def invalid_json_response() -> Mock:
    return _create_response_mock(
        status_code=200,
        json_data=None,
        text="Not a JSON",
        raise_for_status=ValueError("Invalid JSON"),
    )


@pytest.fixture
def async_client_factory(
    valid_uuid: str,
) -> typing.Iterator[typing.Callable[[], AsyncClient]]:
    clients: typing.List[AsyncClient] = []

    def _create_client() -> AsyncClient:
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = Mock()
            mock_instance.is_closed = False
            mock_instance.aclose = AsyncMock()
            mock_client.return_value = mock_instance

            client = AsyncClient(valid_uuid)
            clients.append(client)
            return client

    yield _create_client

    for client in clients:
        if not client.is_closed:
            asyncio.run(client.aclose())


class TestBaseAPIClient:
    def test_init_with_valid_api_key(self, valid_uuid: str) -> None:
        client = SyncClient(valid_uuid)
        assert client._api_key == valid_uuid
        assert client.base_url == BaseAPIClient.DEFAULT_BASE_URL
        assert client.retry_args is not None
        client.close()

    def test_init_with_invalid_api_key(self) -> None:
        with pytest.raises(ValueError) as excinfo:
            SyncClient("invalid-uuid")
        assert "Invalid FACEIT API key format" in str(excinfo.value)
        assert BASE_WIKI_URL in str(excinfo.value)

    def test_init_with_bytes_api_key(self, valid_uuid: str) -> None:
        bytes_key = valid_uuid.encode()
        client = SyncClient(bytes_key)
        assert client._api_key == valid_uuid
        client.close()

    def test_api_key_property(self, valid_uuid: str) -> None:
        client = SyncClient(valid_uuid)
        masked_key = client.api_key
        assert masked_key != valid_uuid
        client.close()

    def test_base_headers(self, valid_uuid: str) -> None:
        client = SyncClient(valid_uuid)
        headers = client._base_headers
        assert headers["Accept"] == "application/json"
        assert headers["Authorization"] == f"Bearer {valid_uuid}"
        client.close()

    def test_create_endpoint(self, valid_uuid: str) -> None:
        client = SyncClient(valid_uuid)
        endpoint = client.create_endpoint("users", "123")
        assert isinstance(endpoint, Endpoint)
        assert str(endpoint) == f"{client.base_url}/users/123"
        client.close()

    def test_prepare_request_with_string(self, valid_uuid: str) -> None:
        client = SyncClient(valid_uuid)
        url, headers = client._prepare_request("users/123")
        assert url == f"{client.base_url}/users/123"
        assert headers == client._base_headers
        client.close()

    def test_prepare_request_with_endpoint(self, valid_uuid: str) -> None:
        client = SyncClient(valid_uuid)
        endpoint = Endpoint("users", "123")
        url, headers = client._prepare_request(endpoint)
        assert url == f"{client.base_url}/users/123"
        assert headers == client._base_headers
        client.close()

    def test_prepare_request_with_custom_headers(self, valid_uuid: str) -> None:
        client = SyncClient(valid_uuid)
        custom_headers = {"X-Custom": "Value"}
        url, headers = client._prepare_request("users/123", custom_headers)
        assert url == f"{client.base_url}/users/123"
        assert headers["X-Custom"] == "Value"
        assert headers["Authorization"] == f"Bearer {valid_uuid}"
        client.close()

    def test_handle_response_success(self, mock_response: Mock) -> None:
        result = BaseAPIClient._handle_response(mock_response)
        assert result == {"data": "test_data"}

    def test_handle_response_http_error(self, error_response: Mock) -> None:
        with pytest.raises(BadRequestError) as excinfo:
            BaseAPIClient._handle_response(error_response)
        assert excinfo.value.status_code == httpx.codes.BAD_REQUEST
        assert excinfo.value.message == httpx.codes.get_reason_phrase(400)
        assert str(excinfo.value) == BadRequestError._MESSAGE_FORMAT.format(
            status_code=excinfo.value.status_code,
            message=httpx.codes.get_reason_phrase(400),
        )

    def test_handle_response_server_error(self, server_error_response: Mock) -> None:
        with pytest.raises(APIError):
            BaseAPIClient._handle_response(server_error_response)

    def test_handle_response_invalid_json(self, invalid_json_response: Mock) -> None:
        with pytest.raises(APIError) as excinfo:
            BaseAPIClient._handle_response(invalid_json_response)
        assert excinfo.value.status_code == httpx.codes.OK
        assert "Invalid JSON response" in excinfo.value.message


class TestSyncClient:
    @patch("httpx.Client")
    def test_init(self, mock_client: Mock, valid_uuid: str) -> None:
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_client.return_value = mock_instance

        client = SyncClient(valid_uuid)
        assert isinstance(client, SyncClient)
        mock_client.assert_called_once()
        client.close()

    @patch("httpx.Client")
    def test_close(self, mock_client: Mock, valid_uuid: str) -> None:
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_client.return_value = mock_instance

        client = SyncClient(valid_uuid)
        client.close()
        mock_instance.close.assert_called_once()

    @patch("httpx.Client")
    def test_context_manager(self, mock_client: Mock, valid_uuid: str) -> None:
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_client.return_value = mock_instance

        with SyncClient(valid_uuid) as client:
            assert isinstance(client, SyncClient)
        mock_instance.close.assert_called_once()

    @patch.object(_BaseSyncClient, "request")
    @pytest.mark.parametrize(
        ("client_method", "endpoint", "call_kwargs", "expected_supported_method"),
        [
            ("get", "users/123", {}, SupportedMethod.GET),
            ("post", "users", {"json": {"name": "test"}}, SupportedMethod.POST),
        ],
    )
    def test_get_post_methods(
        self,
        mock_request: Mock,
        valid_uuid: str,
        client_method: str,
        endpoint: str,
        call_kwargs: typing.Dict[str, typing.Any],
        expected_supported_method: SupportedMethod,
    ) -> None:
        with patch("httpx.Client") as mock_client:
            mock_instance = Mock()
            mock_instance.is_closed = False
            mock_client.return_value = mock_instance

            client = SyncClient(valid_uuid)
            getattr(client, client_method)(endpoint, **call_kwargs)

            assert call_kwargs == {} or "json" in call_kwargs
            mock_request.assert_called_with(
                expected_supported_method,
                endpoint,
                **call_kwargs,
            )
            client.close()

    @patch("httpx.Client")
    def test_request_with_retry(
        self, mock_client: Mock, valid_uuid: str, mock_response: Mock
    ) -> None:
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.request.return_value = mock_response
        mock_client.return_value = mock_instance

        client = SyncClient(
            valid_uuid, retry_args={"stop": tenacity.stop_after_attempt(1)}
        )
        result = client.request(SupportedMethod.GET, "users/123")
        assert result == {"data": "test_data"}
        mock_instance.request.assert_called_once()
        client.close()

    @patch("httpx.Client")
    def test_request_with_timeout(self, mock_client: Mock, valid_uuid: str) -> None:
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.request.side_effect = httpx.TimeoutException("Timeout")
        mock_client.return_value = mock_instance

        client = SyncClient(
            valid_uuid, retry_args={"stop": tenacity.stop_after_attempt(1)}
        )
        with pytest.raises(httpx.TimeoutException):
            client.request(SupportedMethod.GET, "users/123")
        client.close()


class TestAsyncClient:
    async def test_init(
        self, async_client_factory: typing.Callable[[], AsyncClient]
    ) -> None:
        client = async_client_factory()
        assert isinstance(client, AsyncClient)
        await client.aclose()

    async def test_aclose(
        self, async_client_factory: typing.Callable[[], AsyncClient]
    ) -> None:
        client = async_client_factory()
        await client.aclose()
        client._client.aclose.assert_called_once()

    @patch.object(_BaseAsyncClient, "request")
    @pytest.mark.parametrize(
        ("client_method", "endpoint", "call_kwargs", "expected_supported_method"),
        [
            ("get", "users/123", {}, SupportedMethod.GET),
            ("post", "users", {"json": {"name": "test"}}, SupportedMethod.POST),
        ],
    )
    async def test_get_post_methods(
        self,
        mock_request: Mock,
        async_client_factory: typing.Callable[[], AsyncClient],
        client_method: str,
        endpoint: str,
        call_kwargs: typing.Dict[str, typing.Any],
        expected_supported_method: SupportedMethod,
    ) -> None:
        client = async_client_factory()
        mock_request.return_value = {"data": "test_data"}
        await getattr(client, client_method)(endpoint, **call_kwargs)

        mock_request.assert_called_with(
            expected_supported_method,
            endpoint,
            **call_kwargs,
        )
        await client.aclose()

    @patch("httpx.AsyncClient")
    async def test_context_manager(self, mock_client: Mock, valid_uuid: str) -> None:
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.aclose = AsyncMock()
        mock_client.return_value = mock_instance

        async with AsyncClient(valid_uuid) as client:
            assert isinstance(client, AsyncClient)
        mock_instance.aclose.assert_called_once()

    @patch("httpx.AsyncClient")
    async def test_request_with_retry(
        self, mock_client: Mock, valid_uuid: str, mock_response: Mock
    ) -> None:
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.request = AsyncMock(return_value=mock_response)
        mock_instance.aclose = AsyncMock()
        mock_client.return_value = mock_instance

        async with AsyncClient(
            valid_uuid, retry_args={"stop": tenacity.stop_after_attempt(1)}
        ) as client:
            result = await client.request(SupportedMethod.GET, "users/123")
            assert result == {"data": "test_data"}
            mock_instance.request.assert_called_once()

    @patch("httpx.AsyncClient")
    async def test_request_with_timeout(
        self, mock_client: Mock, valid_uuid: str
    ) -> None:
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_instance.aclose = AsyncMock()
        mock_client.return_value = mock_instance

        async with AsyncClient(
            valid_uuid, retry_args={"stop": tenacity.stop_after_attempt(1)}
        ) as client:
            with pytest.raises(httpx.TimeoutException):
                await client.request(SupportedMethod.GET, "users/123")

    @patch("httpx.AsyncClient")
    async def test_close_all(self, mock_client: Mock, valid_uuid: str) -> None:
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.aclose = AsyncMock()
        mock_client.return_value = mock_instance

        clients = []
        try:
            clients = [AsyncClient(valid_uuid) for _ in range(3)]
            await AsyncClient.close_all()

            assert mock_instance.aclose.call_count == 3
        finally:
            for client in clients:
                if not client.is_closed:
                    await client.aclose()

    def test_close_raises_error(self, valid_uuid: str) -> None:
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = Mock()
            mock_instance.is_closed = True
            mock_client.return_value = mock_instance

            client = AsyncClient(valid_uuid)
            try:
                with pytest.raises(RuntimeError) as excinfo:
                    client.close()
                assert "Use 'await AsyncClient.aclose()'" in str(excinfo.value)
            finally:
                asyncio.run(client.aclose())

    async def test_update_rate_limit(
        self, async_client_factory: typing.Callable[[], AsyncClient]
    ) -> None:
        client = async_client_factory()
        try:
            original_max_concurrent_requests = AsyncClient._max_concurrent_requests

            AsyncClient.update_rate_limit(20)
            assert AsyncClient._max_concurrent_requests == 20

            with pytest.warns(UserWarning):
                AsyncClient.update_rate_limit(
                    AsyncClient.MAX_CONCURRENT_REQUESTS_ABSOLUTE + 10
                )
            assert (
                AsyncClient._max_concurrent_requests
                == AsyncClient.MAX_CONCURRENT_REQUESTS_ABSOLUTE
            )

            AsyncClient.update_rate_limit(original_max_concurrent_requests)
        finally:
            await client.aclose()

    async def test_configure_adaptive_limits(
        self, async_client_factory: typing.Callable[[], AsyncClient]
    ) -> None:
        client = async_client_factory()
        try:
            original_threshold = AsyncClient._ssl_error_threshold
            original_min_connections = AsyncClient._min_connections
            original_recovery_interval = AsyncClient._recovery_interval
            original_enabled = AsyncClient._adaptive_limit_enabled

            AsyncClient.configure_adaptive_limits(
                ssl_error_threshold=10,
                min_connections=3,
                recovery_interval=600,
                enabled=False,
            )

            assert AsyncClient._ssl_error_threshold == 10
            assert AsyncClient._min_connections == 3
            assert AsyncClient._recovery_interval == 600
            assert AsyncClient._adaptive_limit_enabled is False

            AsyncClient.configure_adaptive_limits(
                ssl_error_threshold=original_threshold,
                min_connections=original_min_connections,
                recovery_interval=original_recovery_interval,
                enabled=original_enabled,
            )
        finally:
            await client.aclose()


class TestSSLErrorHandling:
    def test_is_ssl_error(self) -> None:
        assert is_ssl_error(ssl.SSLError("SSL Error"))
        assert is_ssl_error(httpx.ConnectError("SSL connection failed"))
        assert is_ssl_error(httpx.ConnectError("TLS handshake failed"))
        assert not is_ssl_error(ValueError("Not an SSL error"))

    @patch("httpx.AsyncClient")
    async def test_register_ssl_error(self, mock_client: Mock, valid_uuid: str) -> None:
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.aclose = AsyncMock()
        mock_client.return_value = mock_instance

        async with AsyncClient(valid_uuid):
            original_update_rate_limit = AsyncClient.update_rate_limit

            try:
                mock_update_rate_limit = Mock()
                AsyncClient.update_rate_limit = classmethod(
                    lambda _, new_limit: mock_update_rate_limit(new_limit)
                )

                original_ssl_error_count = AsyncClient._ssl_error_count
                original_adaptive_limit_enabled = AsyncClient._adaptive_limit_enabled
                original_max_concurrent_requests = AsyncClient._max_concurrent_requests
                original_ssl_error_threshold = AsyncClient._ssl_error_threshold
                original_min_connections = AsyncClient._min_connections

                AsyncClient._ssl_error_count = 0
                AsyncClient._adaptive_limit_enabled = True
                AsyncClient._max_concurrent_requests = 30
                AsyncClient._ssl_error_threshold = 5
                AsyncClient._min_connections = 5

                result = AsyncClient._register_ssl_error()
                assert result is True
                assert AsyncClient._ssl_error_count == 1
                mock_update_rate_limit.assert_not_called()

                AsyncClient._ssl_error_count = AsyncClient._ssl_error_threshold - 1
                result = AsyncClient._register_ssl_error()
                assert result is True
                mock_update_rate_limit.assert_called_once_with(15)
                assert AsyncClient._ssl_error_count == 0

            finally:
                AsyncClient.update_rate_limit = original_update_rate_limit

                AsyncClient._ssl_error_count = original_ssl_error_count
                AsyncClient._adaptive_limit_enabled = original_adaptive_limit_enabled
                AsyncClient._max_concurrent_requests = original_max_concurrent_requests
                AsyncClient._ssl_error_threshold = original_ssl_error_threshold
                AsyncClient._min_connections = original_min_connections

    @patch("httpx.AsyncClient")
    async def test_check_connection_recovery(
        self, mock_client: Mock, valid_uuid: str
    ) -> None:
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.aclose = AsyncMock()
        mock_client.return_value = mock_instance

        async with AsyncClient(valid_uuid):
            original_update_rate_limit = AsyncClient.update_rate_limit

            try:
                mock_update_rate_limit = Mock()
                AsyncClient.update_rate_limit = classmethod(
                    lambda _, new_limit: mock_update_rate_limit(new_limit)
                )

                original_max_concurrent_requests = AsyncClient._max_concurrent_requests
                original_initial_max_requests = AsyncClient._initial_max_requests
                original_last_ssl_error_time = AsyncClient._last_ssl_error_time
                original_recovery_check_time = AsyncClient._recovery_check_time
                original_recovery_interval = AsyncClient._recovery_interval

                AsyncClient._max_concurrent_requests = 10
                AsyncClient._initial_max_requests = 30
                AsyncClient._last_ssl_error_time = (
                    time() - AsyncClient._recovery_interval - 10
                )
                AsyncClient._recovery_check_time = 0

                await AsyncClient._check_connection_recovery()

                mock_update_rate_limit.assert_called_once_with(15)

            finally:
                AsyncClient.update_rate_limit = original_update_rate_limit

                AsyncClient._max_concurrent_requests = original_max_concurrent_requests
                AsyncClient._initial_max_requests = original_initial_max_requests
                AsyncClient._last_ssl_error_time = original_last_ssl_error_time
                AsyncClient._recovery_check_time = original_recovery_check_time
                AsyncClient._recovery_interval = original_recovery_interval


class TestRetryLogic:
    def test_retry_predicate(
        self, server_error_response: Mock, error_response: Mock
    ) -> None:
        retry_predicate = BaseAPIClient.DEFAULT_RETRY_ARGS["retry"].predicate
        assert retry_predicate(httpx.TimeoutException("Timeout"))
        assert retry_predicate(httpx.ConnectError("Connection failed"))
        assert retry_predicate(httpx.RemoteProtocolError("Protocol error"))
        assert retry_predicate(APIError(server_error_response))
        assert not retry_predicate(
            httpx.HTTPStatusError(
                "Client error", request=Mock(), response=error_response
            )
        )
        assert not retry_predicate(ValueError("Random error"))

    async def test_ssl_before_sleep(self, valid_uuid: str) -> None:
        with patch("httpx.AsyncClient") as mock_client, patch(
            "faceit.http.client._logger"
        ) as mock_logger, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_instance = Mock()
            mock_instance.is_closed = False
            mock_instance.aclose = AsyncMock()
            mock_client.return_value = mock_instance

            custom_retry_args = {
                "before_sleep": lambda _: None,
            }

            async with AsyncClient(valid_uuid, retry_args=custom_retry_args) as client:
                retry_state = Mock()
                retry_state.args = ("https://test.com/api",)
                retry_state.kwargs = {}
                retry_state.outcome = Mock()
                retry_state.outcome.exception.return_value = ssl.SSLError("SSL Error")

                retry_state.attempt_number = 2
                next_action = Mock()
                next_action.sleep = 1.5
                retry_state.next_action = next_action

                before_sleep = client.retry_args["before_sleep"]

                await before_sleep(retry_state)

                mock_sleep.assert_called_once_with(0.5)

                mock_logger.warning.assert_called_with(
                    "SSL connection error to %s",
                    "https://test.com/api",
                )
