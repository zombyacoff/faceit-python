"""NOTE TO DEVELOPERS:

These tests were generated with the assistance of AI and may require
additional review or adjustments. Please verify that all test cases
properly cover the expected behavior of the HTTP client, especially
regarding edge cases, asynchronous behavior, and error handling.
Some tests may need refinement to ensure they don't hang or cause
resource leaks in the test environment.
"""

import asyncio
import ssl
from time import time
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from tenacity import stop_after_attempt

from faceit.constants import BASE_WIKI_URL
from faceit.exceptions import APIError
from faceit.http import AsyncClient, Endpoint, SupportedMethod, SyncClient
from faceit.http.client import (
    BaseAPIClient,
    _BaseAsyncClient,
    _BaseSyncClient,
    is_ssl_error,
)
from faceit.utils import REDACTED_MARKER


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"data": "test_data"}
    response.raise_for_status.return_value = None
    response.url = "https://test.com/api"
    response.text = '{"data": "test_data"}'
    return response


@pytest.fixture
def error_response():
    """Create a mock HTTP error response."""
    response = Mock()
    response.status_code = 400
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad Request", request=Mock(), response=response
    )
    response.url = "https://test.com/api"
    response.text = "Bad Request"
    response.is_server_error = False
    return response


@pytest.fixture
def server_error_response():
    """Create a mock HTTP server error response."""
    response = Mock()
    response.status_code = 500
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Internal Server Error", request=Mock(), response=response
    )
    response.url = "https://test.com/api"
    response.text = "Internal Server Error"
    response.is_server_error = True
    return response


@pytest.fixture
def invalid_json_response():
    """Create a mock response with invalid JSON."""
    response = Mock()
    response.status_code = 200
    response.json.side_effect = ValueError("Invalid JSON")
    response.raise_for_status.return_value = None
    response.url = "https://test.com/api"
    response.text = "Not a JSON"
    return response


@pytest.fixture
def async_client_factory(valid_uuid):
    """Factory fixture that creates AsyncClient instances."""
    clients = []

    def _create_client():
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = Mock()
            mock_instance.is_closed = False
            mock_instance.aclose = AsyncMock()
            mock_client.return_value = mock_instance

            client = AsyncClient(valid_uuid)
            clients.append(client)
            return client

    yield _create_client

    # Clean up any clients that weren't closed
    for client in clients:
        if not client.is_closed:
            asyncio.run(client.aclose())


# Test Base Client
class TestBaseAPIClient:
    """Tests for the BaseAPIClient class."""

    def test_init_with_valid_api_key(self, valid_uuid):
        """Test initialization with a valid API key."""
        # We need to use a concrete subclass for testing
        client = SyncClient(valid_uuid)
        assert client._api_key == valid_uuid
        assert client.base_url == BaseAPIClient.DEFAULT_BASE_URL
        assert client.retry_args is not None
        client.close()  # Ensure proper cleanup

    def test_init_with_invalid_api_key(self):
        """Test initialization with an invalid API key."""
        with pytest.raises(ValueError) as excinfo:
            SyncClient("invalid-uuid")
        assert "Invalid FACEIT API key format" in str(excinfo.value)
        assert BASE_WIKI_URL in str(excinfo.value)

    def test_init_with_bytes_api_key(self, valid_uuid):
        """Test initialization with a bytes API key."""
        bytes_key = valid_uuid.encode()
        client = SyncClient(bytes_key)
        assert client._api_key == valid_uuid
        client.close()  # Ensure proper cleanup

    def test_api_key_property(self, valid_uuid):
        """Test that the api_key property masks the actual key."""
        client = SyncClient(valid_uuid)
        masked_key = client.api_key
        assert masked_key != valid_uuid
        assert masked_key == REDACTED_MARKER
        client.close()  # Ensure proper cleanup

    def test_base_headers(self, valid_uuid):
        """Test that base headers are correctly constructed."""
        client = SyncClient(valid_uuid)
        headers = client._base_headers
        assert headers["Accept"] == "application/json"
        assert headers["Authorization"] == f"Bearer {valid_uuid}"
        client.close()  # Ensure proper cleanup

    def test_create_endpoint(self, valid_uuid):
        """Test endpoint creation."""
        client = SyncClient(valid_uuid)
        endpoint = client.create_endpoint("users", "123")
        assert isinstance(endpoint, Endpoint)
        assert str(endpoint) == f"{client.base_url}/users/123"
        client.close()  # Ensure proper cleanup

    def test_prepare_request_with_string(self, valid_uuid):
        """Test request preparation with a string endpoint."""
        client = SyncClient(valid_uuid)
        url, headers = client._prepare_request("users/123")
        assert url == f"{client.base_url}/users/123"
        assert headers == client._base_headers
        client.close()  # Ensure proper cleanup

    def test_prepare_request_with_endpoint(self, valid_uuid):
        """Test request preparation with an Endpoint object."""
        client = SyncClient(valid_uuid)
        endpoint = Endpoint("users", "123")
        url, headers = client._prepare_request(endpoint)
        assert url == f"{client.base_url}/users/123"
        assert headers == client._base_headers
        client.close()  # Ensure proper cleanup

    def test_prepare_request_with_custom_headers(self, valid_uuid):
        """Test request preparation with custom headers."""
        client = SyncClient(valid_uuid)
        custom_headers = {"X-Custom": "Value"}
        url, headers = client._prepare_request("users/123", custom_headers)
        assert url == f"{client.base_url}/users/123"
        assert headers["X-Custom"] == "Value"
        assert headers["Authorization"] == f"Bearer {valid_uuid}"
        client.close()  # Ensure proper cleanup

    def test_handle_response_success(self, mock_response):
        """Test successful response handling."""
        result = BaseAPIClient._handle_response(mock_response)
        assert result == {"data": "test_data"}

    def test_handle_response_http_error(self, error_response):
        """Test HTTP error response handling."""
        with pytest.raises(APIError) as excinfo:
            BaseAPIClient._handle_response(error_response)
        assert excinfo.value.status_code == 400
        assert excinfo.value.message == "Bad Request"

    def test_handle_response_server_error(self, server_error_response):
        """Test server error response handling."""
        with pytest.raises(httpx.HTTPStatusError):
            BaseAPIClient._handle_response(server_error_response)

    def test_handle_response_invalid_json(self, invalid_json_response):
        """Test handling of responses with invalid JSON."""
        with pytest.raises(APIError) as excinfo:
            BaseAPIClient._handle_response(invalid_json_response)
        assert excinfo.value.status_code == 200
        assert "Invalid JSON response" in excinfo.value.message


# Test Sync Client
class TestSyncClient:
    """Tests for the SyncClient class."""

    @patch("httpx.Client")
    def test_init(self, mock_client, valid_uuid):
        """Test SyncClient initialization."""
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_client.return_value = mock_instance

        client = SyncClient(valid_uuid)
        assert isinstance(client, SyncClient)
        mock_client.assert_called_once()
        client.close()  # Ensure proper cleanup

    @patch("httpx.Client")
    def test_close(self, mock_client, valid_uuid):
        """Test client close method."""
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_client.return_value = mock_instance

        client = SyncClient(valid_uuid)
        client.close()
        mock_instance.close.assert_called_once()

    @patch("httpx.Client")
    def test_context_manager(self, mock_client, valid_uuid):
        """Test client as context manager."""
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_client.return_value = mock_instance

        with SyncClient(valid_uuid) as client:
            assert isinstance(client, SyncClient)
        mock_instance.close.assert_called_once()

    @patch.object(_BaseSyncClient, "request")
    def test_get_method(self, mock_request, valid_uuid):
        """Test get method."""
        with patch("httpx.Client") as mock_client:
            mock_instance = Mock()
            mock_instance.is_closed = False
            mock_client.return_value = mock_instance

            client = SyncClient(valid_uuid)
            client.get("users/123")
            mock_request.assert_called_with(SupportedMethod.GET, "users/123")
            client.close()  # Ensure proper cleanup

    @patch.object(_BaseSyncClient, "request")
    def test_post_method(self, mock_request, valid_uuid):
        """Test post method."""
        with patch("httpx.Client") as mock_client:
            mock_instance = Mock()
            mock_instance.is_closed = False
            mock_client.return_value = mock_instance

            client = SyncClient(valid_uuid)
            client.post("users", json={"name": "test"})
            mock_request.assert_called_with(
                SupportedMethod.POST, "users", json={"name": "test"}
            )
            client.close()  # Ensure proper cleanup

    @patch("httpx.Client")
    def test_request_with_retry(self, mock_client, valid_uuid, mock_response):
        """Test request with retry logic."""
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.request.return_value = mock_response
        mock_client.return_value = mock_instance

        client = SyncClient(valid_uuid, retry_args={"stop": stop_after_attempt(1)})
        result = client.request(SupportedMethod.GET, "users/123")
        assert result == {"data": "test_data"}
        mock_instance.request.assert_called_once()
        client.close()  # Ensure proper cleanup

    @patch("httpx.Client")
    def test_request_with_timeout(self, mock_client, valid_uuid):
        """Test request with timeout."""
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.request.side_effect = httpx.TimeoutException("Timeout")
        mock_client.return_value = mock_instance

        client = SyncClient(valid_uuid, retry_args={"stop": stop_after_attempt(1)})
        with pytest.raises(httpx.TimeoutException):
            client.request(SupportedMethod.GET, "users/123")
        client.close()  # Ensure proper cleanup


# Test Async Client
class TestAsyncClient:
    """Tests for the AsyncClient class."""

    @pytest.mark.asyncio
    async def test_init(self, async_client_factory):
        """Test AsyncClient initialization."""
        client = async_client_factory()
        assert isinstance(client, AsyncClient)
        await client.aclose()

    @pytest.mark.asyncio
    async def test_aclose(self, async_client_factory):
        """Test client aclose method."""
        client = async_client_factory()
        await client.aclose()
        client._client.aclose.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(_BaseAsyncClient, "request")
    async def test_get_method(self, mock_request, async_client_factory):
        """Test get method."""
        client = async_client_factory()
        mock_request.return_value = {"data": "test_data"}
        await client.get("users/123")
        mock_request.assert_called_with(SupportedMethod.GET, "users/123")
        await client.aclose()

    @pytest.mark.asyncio
    @patch.object(_BaseAsyncClient, "request")
    async def test_post_method(self, mock_request, async_client_factory):
        """Test post method."""
        client = async_client_factory()
        mock_request.return_value = {"data": "test_data"}
        await client.post("users", json={"name": "test"})
        mock_request.assert_called_with(
            SupportedMethod.POST, "users", json={"name": "test"}
        )
        await client.aclose()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_context_manager(self, mock_client, valid_uuid):
        """Test client as async context manager."""
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.aclose = AsyncMock()
        mock_client.return_value = mock_instance

        async with AsyncClient(valid_uuid) as client:
            assert isinstance(client, AsyncClient)
        mock_instance.aclose.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_request_with_retry(self, mock_client, valid_uuid, mock_response):
        """Test request with retry logic."""
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.request = AsyncMock(return_value=mock_response)
        mock_instance.aclose = AsyncMock()
        mock_client.return_value = mock_instance

        async with AsyncClient(
            valid_uuid, retry_args={"stop": stop_after_attempt(1)}
        ) as client:
            result = await client.request(SupportedMethod.GET, "users/123")
            assert result == {"data": "test_data"}
            mock_instance.request.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_request_with_timeout(self, mock_client, valid_uuid):
        """Test request with timeout."""
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_instance.aclose = AsyncMock()
        mock_client.return_value = mock_instance

        async with AsyncClient(
            valid_uuid, retry_args={"stop": stop_after_attempt(1)}
        ) as client:
            with pytest.raises(httpx.TimeoutException):
                await client.request(SupportedMethod.GET, "users/123")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_close_all(self, mock_client, valid_uuid):
        """Test close_all class method."""
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.aclose = AsyncMock()
        mock_client.return_value = mock_instance

        # Create multiple clients and track them for cleanup
        clients = []
        try:
            clients = [AsyncClient(valid_uuid) for _ in range(3)]
            await AsyncClient.close_all()

            # Each client should have aclose called once
            assert mock_instance.aclose.call_count == 3
        finally:
            # Ensure all clients are closed even if the test fails
            for client in clients:
                if not client.is_closed:
                    await client.aclose()

    def test_close_raises_error(self, valid_uuid):
        """Test that close method raises TypeError."""
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
                # Clean up properly
                asyncio.run(client.aclose())

    @pytest.mark.asyncio
    async def test_update_rate_limit(self, async_client_factory):
        """Test update_rate_limit class method."""
        client = async_client_factory()
        try:
            # Save original value to restore later
            original_max_concurrent_requests = AsyncClient._max_concurrent_requests

            # Test updating to a valid value
            AsyncClient.update_rate_limit(20)
            assert AsyncClient._max_concurrent_requests == 20

            # Test updating to a value exceeding maximum
            with pytest.warns(UserWarning):
                AsyncClient.update_rate_limit(
                    AsyncClient.MAX_CONCURRENT_REQUESTS_ABSOLUTE + 10
                )
            assert (
                AsyncClient._max_concurrent_requests
                == AsyncClient.MAX_CONCURRENT_REQUESTS_ABSOLUTE
            )

            # Restore original value
            AsyncClient.update_rate_limit(original_max_concurrent_requests)
        finally:
            await client.aclose()

    @pytest.mark.asyncio
    async def test_configure_adaptive_limits(self, async_client_factory):
        """Test configure_adaptive_limits class method."""
        client = async_client_factory()
        try:
            # Save original values
            original_threshold = AsyncClient._ssl_error_threshold
            original_min_connections = AsyncClient._min_connections
            original_recovery_interval = AsyncClient._recovery_interval
            original_enabled = AsyncClient._adaptive_limit_enabled

            # Test updating all values
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

            # Restore original values
            AsyncClient.configure_adaptive_limits(
                ssl_error_threshold=original_threshold,
                min_connections=original_min_connections,
                recovery_interval=original_recovery_interval,
                enabled=original_enabled,
            )
        finally:
            await client.aclose()


# Test SSL Error Handling
class TestSSLErrorHandling:
    """Tests for SSL error handling functionality."""

    def testis_ssl_error(self):
        """Test the is_ssl_error function."""
        # Test with SSLError
        assert is_ssl_error(ssl.SSLError("SSL Error"))

        # Test with ConnectError containing SSL in message
        assert is_ssl_error(httpx.ConnectError("SSL connection failed"))

        # Test with ConnectError containing TLS in message
        assert is_ssl_error(httpx.ConnectError("TLS handshake failed"))

        # Test with non-SSL error
        assert not is_ssl_error(ValueError("Not an SSL error"))

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch("faceit.http.client._logger")  # Mock the logger to avoid real logs
    async def test_register_ssl_error(self, mock_logger, mock_client, valid_uuid):
        """Test _register_ssl_error method."""
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.aclose = AsyncMock()
        mock_client.return_value = mock_instance

        async with AsyncClient(valid_uuid) as client:
            # Save the original update_rate_limit method
            original_update_rate_limit = AsyncClient.update_rate_limit

            try:
                # Create a mock for update_rate_limit
                mock_update_rate_limit = Mock()
                AsyncClient.update_rate_limit = classmethod(
                    lambda cls, new_limit: mock_update_rate_limit(new_limit)
                )

                # Save original values
                original_ssl_error_count = AsyncClient._ssl_error_count
                original_adaptive_limit_enabled = AsyncClient._adaptive_limit_enabled
                original_max_concurrent_requests = AsyncClient._max_concurrent_requests
                original_ssl_error_threshold = AsyncClient._ssl_error_threshold
                original_min_connections = AsyncClient._min_connections

                # Set up conditions for the test
                AsyncClient._ssl_error_count = 0
                AsyncClient._adaptive_limit_enabled = True
                AsyncClient._max_concurrent_requests = 30
                AsyncClient._ssl_error_threshold = 5
                AsyncClient._min_connections = 5

                # Test 1: Error registration increases the counter
                result = AsyncClient._register_ssl_error()
                assert result is True
                assert AsyncClient._ssl_error_count == 1
                mock_update_rate_limit.assert_not_called()

                # Test 2: Reaching the threshold triggers rate limit reduction
                AsyncClient._ssl_error_count = AsyncClient._ssl_error_threshold - 1
                result = AsyncClient._register_ssl_error()
                assert result is True
                mock_update_rate_limit.assert_called_once_with(15)  # 30 // 2 = 15
                assert AsyncClient._ssl_error_count == 0  # Counter should be reset

            finally:
                # Restore the original method
                AsyncClient.update_rate_limit = original_update_rate_limit

                # Restore original values
                AsyncClient._ssl_error_count = original_ssl_error_count
                AsyncClient._adaptive_limit_enabled = original_adaptive_limit_enabled
                AsyncClient._max_concurrent_requests = original_max_concurrent_requests
                AsyncClient._ssl_error_threshold = original_ssl_error_threshold
                AsyncClient._min_connections = original_min_connections

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch("faceit.http.client._logger")  # Mock the logger to avoid real logs
    async def test_check_connection_recovery(
        self, mock_logger, mock_client, valid_uuid
    ):
        """Test _check_connection_recovery method."""
        mock_instance = Mock()
        mock_instance.is_closed = False
        mock_instance.aclose = AsyncMock()
        mock_client.return_value = mock_instance

        async with AsyncClient(valid_uuid) as client:
            # Save the original update_rate_limit method
            original_update_rate_limit = AsyncClient.update_rate_limit

            try:
                # Create a mock for update_rate_limit
                mock_update_rate_limit = Mock()
                AsyncClient.update_rate_limit = classmethod(
                    lambda cls, new_limit: mock_update_rate_limit(new_limit)
                )

                # Save original values
                original_max_concurrent_requests = AsyncClient._max_concurrent_requests
                original_initial_max_requests = AsyncClient._initial_max_requests
                original_last_ssl_error_time = AsyncClient._last_ssl_error_time
                original_recovery_check_time = AsyncClient._recovery_check_time
                original_recovery_interval = AsyncClient._recovery_interval

                # Set up conditions for the test
                AsyncClient._max_concurrent_requests = 10
                AsyncClient._initial_max_requests = 30
                AsyncClient._last_ssl_error_time = (
                    time() - AsyncClient._recovery_interval - 10
                )
                AsyncClient._recovery_check_time = 0

                # Call the method
                await AsyncClient._check_connection_recovery()

                # Check that update_rate_limit was called with the correct value
                # New limit should be min(30, 10 + max(1, 10 // 2)) = min(30, 10 + 5) = 15
                mock_update_rate_limit.assert_called_once_with(15)

                # Check that the logger was called with the correct arguments
                mock_logger.info.assert_called_once()

            finally:
                # Restore the original method
                AsyncClient.update_rate_limit = original_update_rate_limit

                # Restore original values
                AsyncClient._max_concurrent_requests = original_max_concurrent_requests
                AsyncClient._initial_max_requests = original_initial_max_requests
                AsyncClient._last_ssl_error_time = original_last_ssl_error_time
                AsyncClient._recovery_check_time = original_recovery_check_time
                AsyncClient._recovery_interval = original_recovery_interval


# Test Retry Logic
class TestRetryLogic:
    """Tests for retry logic."""

    def test_retry_predicate(self):
        """Test the retry predicate in DEFAULT_RETRY_ARGS."""
        retry_predicate = BaseAPIClient.DEFAULT_RETRY_ARGS["retry"].predicate

        # Should retry on timeout
        assert retry_predicate(httpx.TimeoutException("Timeout"))

        # Should retry on connection error
        assert retry_predicate(httpx.ConnectError("Connection failed"))

        # Should retry on protocol error
        assert retry_predicate(httpx.RemoteProtocolError("Protocol error"))

        # Should retry on server error
        response = Mock()
        response.is_server_error = True
        assert retry_predicate(
            httpx.HTTPStatusError("Server error", request=Mock(), response=response)
        )

        # Should not retry on client error
        response = Mock()
        response.is_server_error = False
        assert not retry_predicate(
            httpx.HTTPStatusError("Client error", request=Mock(), response=response)
        )

        # Should not retry on other exceptions
        assert not retry_predicate(ValueError("Random error"))

    @pytest.mark.asyncio
    async def test_ssl_before_sleep(self, valid_uuid):
        """Test the SSL before_sleep callback."""
        with patch("httpx.AsyncClient") as mock_client, patch(
            "faceit.http.client._logger"
        ) as mock_logger, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_instance = Mock()
            mock_instance.is_closed = False
            mock_instance.aclose = AsyncMock()
            mock_client.return_value = mock_instance

            # Create a custom retry_args with a simple before_sleep function
            # that doesn't use the default logger format
            custom_retry_args = {
                "before_sleep": lambda _: None,  # Simple no-op function
            }

            async with AsyncClient(valid_uuid, retry_args=custom_retry_args) as client:
                # Create a more complete mock for RetryCallState
                retry_state = Mock()
                retry_state.args = ("https://test.com/api",)
                retry_state.kwargs = {}
                retry_state.outcome = Mock()
                retry_state.outcome.exception.return_value = ssl.SSLError("SSL Error")

                # Add attributes needed for logger message formatting
                retry_state.attempt_number = 2
                next_action = Mock()
                next_action.sleep = 1.5
                retry_state.next_action = next_action

                # Get the before_sleep callback
                before_sleep = client.retry_args["before_sleep"]

                # Call the callback
                await before_sleep(retry_state)

                # Check that sleep was called with the correct delay
                mock_sleep.assert_called_once_with(0.5)

                # Verify that the logger was called with the SSL error message
                mock_logger.warning.assert_called_with(
                    "SSL connection error to %s",
                    "https://test.com/api",
                )
