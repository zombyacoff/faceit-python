from __future__ import annotations

import asyncio
import logging
import ssl
import typing as t
import warnings
from abc import ABC, abstractmethod
from enum import auto
from inspect import iscoroutinefunction
from threading import Lock
from time import time
from weakref import WeakSet

import httpx
from pydantic import PositiveInt, validate_call
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from faceit import _repr
from faceit._utils import validate_uuid_args
from faceit.constants import BASE_WIKI_URL, FaceitStrEnum
from faceit.exceptions import FaceitAPIError

from ._helpers import Endpoint

if t.TYPE_CHECKING:
    from types import TracebackType

    from faceit._types import (
        APIResponse,
        EndpointParam,
        RawAPIItem,
        RawAPIPageResponse,
        Self,
    )

_logger = logging.getLogger(__name__)

_HttpxClientT = t.TypeVar(
    "_HttpxClientT", bound=t.Union[httpx.Client, httpx.AsyncClient]
)


@t.final
class SupportedMethod(FaceitStrEnum):
    GET = auto()
    POST = auto()


@_repr.representation("api_key", "base_url", "retry_args")
class BaseAPIClient(t.Generic[_HttpxClientT], ABC):
    __slots__ = "_api_key", "base_url", "retry_args"

    DEFAULT_BASE_URL: t.Final = "https://open.faceit.com/data/v4"
    DEFAULT_TIMEOUT: float = 10
    DEFAULT_RETRY_ARGS: t.Dict[str, t.Any] = {
        "stop": stop_after_attempt(3),
        "wait": wait_random_exponential(multiplier=1, max=10),
        # Retry on transient errors:
        # network issues (timeouts, connection errors, protocol errors)
        # and server errors (5xx HTTP status codes)
        "retry": retry_if_exception(
            lambda e: isinstance(
                e,
                (
                    httpx.TimeoutException,
                    httpx.ConnectError,
                    httpx.RemoteProtocolError,
                ),
            )
            or (
                isinstance(e, httpx.HTTPStatusError)
                and e.response.is_server_error
            )
        ),
        "reraise": True,
        # Log retry attempt details before sleeping
        "before_sleep": lambda s: _logger.warning(
            "Retry attempt %d failed; sleeping for %.2f seconds before next attempt",
            s.attempt_number,
            s.next_action.sleep if s.next_action else 0,
        ),
    }

    _client: _HttpxClientT  # Type hint for the HTTP client that subclasses must initialize

    # NOTE: The API key must be a valid UUID
    # Type hint remains as `str` for clarity, though other
    # convertible types (e.g., `UUID`, `bytes`) are accepted
    @validate_uuid_args(
        "api_key",
        error_message=f"Invalid FACEIT API key format. "
        f"Please visit the official wiki for API key information: "
        f"{BASE_WIKI_URL}/getting-started/authentication/api-keys",
    )
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        retry_args: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        # Handle edge case where `api_key` is `bytes` (passes UUID validation)
        # Convert to string instead of raising an exception
        self._api_key = (
            api_key.decode() if isinstance(api_key, bytes) else str(api_key)
        )
        self.retry_args = {
            **self.__class__.DEFAULT_RETRY_ARGS,
            **(retry_args or {}),
        }

    @property
    def api_key(self) -> str:
        return f"{self._api_key[:4]}...{self._api_key[-4:]}"

    @property
    def _base_headers(self) -> t.Dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

    # Provide read-only access to the underlying client for
    # exceptional cases where direct interaction might be necessary,
    # while keeping the interface immutable
    @property
    def raw_client(self) -> _HttpxClientT:
        return self._client

    @property
    def is_closed(self) -> bool:
        # Defensive check to handle cases where client initialization failed
        # Prevents AttributeError in __del__ during garbage collection
        return self._client.is_closed if hasattr(self, "_client") else True

    def create_endpoint(self, *path_parts: str) -> Endpoint:
        return Endpoint(*path_parts, base_path=self.base_url)

    def _prepare_request(
        self,
        endpoint: EndpointParam,
        headers: t.Optional[t.Dict[str, str]] = None,
    ) -> t.Tuple[str, t.Dict[str, str]]:
        return str(
            endpoint.with_base(self.base_url)
            if isinstance(endpoint, Endpoint)
            else self.create_endpoint(endpoint)
        ), {**self._base_headers, **(headers or {})}

    @staticmethod
    def _handle_response(response: httpx.Response) -> APIResponse:
        try:
            response.raise_for_status()
            _logger.debug("Successful response from %s", response.url)
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.is_server_error:
                _logger.warning(
                    "Server error %s at %s, will retry if applicable",
                    e.response.status_code,
                    response.url,
                )
                raise
            _logger.exception(
                "HTTP error %s at %s: %s",
                response.status_code,
                response.url,
                response.text,
            )
            raise FaceitAPIError(response.status_code, response.text) from e
        except (ValueError, httpx.DecodingError):
            _logger.exception(
                "Invalid JSON response from %s: %s",
                response.url,
                response.text,
            )
            raise FaceitAPIError(
                response.status_code, "Invalid JSON response"
            ) from None

    def _warn_unclosed_client(self, *, asynchronous: bool = False) -> None:
        warnings.warn(
            f"Unclosed client session detected. Resources may be leaked. "
            f"Use '{'async ' if asynchronous else ''}with' or call "
            f"'{'await client.a' if asynchronous else 'client.'}close()' to close the session properly. "
            f"Relying on __del__ for resource cleanup is not recommended.",
            ResourceWarning,
            stacklevel=2,
        )
        _logger.warning(
            "Unclosed %s instance garbage collected. Resources may be leaked.",
            self.__class__.__name__,
        )

    @abstractmethod
    def __del__(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class _BaseSyncClient(BaseAPIClient[httpx.Client]):
    __slots__ = ("_client",)

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BaseAPIClient.DEFAULT_BASE_URL,
        timeout: float = BaseAPIClient.DEFAULT_TIMEOUT,
        retry_args: t.Optional[t.Dict[str, t.Any]] = None,
        **raw_client_kwargs: t.Any,
    ) -> None:
        super().__init__(api_key, base_url, retry_args)
        self._client = httpx.Client(
            timeout=timeout, headers=self._base_headers, **raw_client_kwargs
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        typ: t.Optional[t.Type[BaseException]],
        exc: t.Optional[BaseException],
        tb: t.Optional[TracebackType],
    ) -> None:
        del typ, exc, tb  # Unused variables, but required for __exit__
        self.close()

    def __del__(self) -> None:
        if not self.is_closed:
            self._warn_unclosed_client()

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        if not self.is_closed:
            self._client.close()
            _logger.debug("%s closed", self.__class__.__name__)

    def request(
        self, method: str, endpoint: EndpointParam, **kwargs: t.Any
    ) -> APIResponse:
        url, headers = self._prepare_request(
            endpoint, kwargs.pop("headers", None)
        )
        retryer = Retrying(**self.retry_args)
        return retryer(
            lambda: self.__class__._handle_response(
                self._client.request(method, url, headers=headers, **kwargs)
            )
        )


def _is_ssl_error(exception: BaseException) -> bool:
    return isinstance(exception, ssl.SSLError) or (
        isinstance(exception, httpx.ConnectError)
        and ("SSL" in str(exception) or "TLS" in str(exception))
    )


# NOTE: Logic on eliminating SSL errors was added because during tests
# it was found that such errors often pop up even with a small
# number of concurrent requests, probably problems on the FACEIT API side
class _BaseAsyncClient(BaseAPIClient[httpx.AsyncClient]):
    __slots__ = "__weakref__", "_client"

    _instances: WeakSet[_BaseAsyncClient] = WeakSet()

    _semaphore: t.Optional[asyncio.Semaphore] = None
    _rate_limit_lock: Lock = Lock()
    _ssl_error_count: int = 0
    _adaptive_limit_enabled: bool = True
    _last_ssl_error_time: float = time()
    _recovery_check_time: float = 0

    # Current limit value is based on empirical testing,
    # but requires further investigation for optimal setting
    MAX_CONCURRENT_REQUESTS: t.Final = 100

    DEFAULT_MAX_CONCURRENT_REQUESTS: int = 30
    DEFAULT_SSL_ERROR_THRESHOLD: int = 5
    DEFAULT_MIN_CONNECTIONS: int = 5
    DEFAULT_RECOVERY_INTERVAL: int = 300
    DEFAULT_KEEPALIVE_EXPIRY: float = 30

    _ssl_error_threshold: int = DEFAULT_SSL_ERROR_THRESHOLD
    _min_connections: int = DEFAULT_MIN_CONNECTIONS
    _max_concurrent_requests: int = DEFAULT_MAX_CONCURRENT_REQUESTS
    _recovery_interval: int = DEFAULT_RECOVERY_INTERVAL
    _initial_max_requests: int = DEFAULT_MAX_CONCURRENT_REQUESTS

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BaseAPIClient.DEFAULT_BASE_URL,
        timeout: float = BaseAPIClient.DEFAULT_TIMEOUT,
        retry_args: t.Optional[t.Dict[str, t.Any]] = None,
        max_concurrent_requests: int = DEFAULT_MAX_CONCURRENT_REQUESTS,
        ssl_error_threshold: int = DEFAULT_SSL_ERROR_THRESHOLD,
        min_connections: int = DEFAULT_MIN_CONNECTIONS,
        recovery_interval: int = DEFAULT_RECOVERY_INTERVAL,
        **raw_client_kwargs: t.Any,
    ) -> None:
        super().__init__(api_key, base_url, retry_args)

        self.__class__._update_initial_max_requests(max_concurrent_requests)

        if (
            ssl_error_threshold != self.__class__.DEFAULT_SSL_ERROR_THRESHOLD
            or min_connections != self.__class__.DEFAULT_MIN_CONNECTIONS
            or recovery_interval != self.__class__.DEFAULT_RECOVERY_INTERVAL
        ):
            self.__class__.configure_adaptive_limits(
                ssl_error_threshold, min_connections, recovery_interval
            )

        # Initialize the client
        limits = raw_client_kwargs.pop("limits", None) or httpx.Limits(
            max_keepalive_connections=max_concurrent_requests,
            max_connections=max_concurrent_requests * 2,
            keepalive_expiry=self.__class__.DEFAULT_KEEPALIVE_EXPIRY,
        )
        transport = raw_client_kwargs.pop(
            "transport", None
        ) or httpx.AsyncHTTPTransport(retries=1)

        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=self._base_headers,
            limits=limits,
            transport=transport,
            **raw_client_kwargs,
        )

        # Initialize or update the semaphore if needed
        if (
            self.__class__._semaphore is None
            or max_concurrent_requests
            != self.__class__._max_concurrent_requests
        ):
            self.__class__.update_rate_limit(max_concurrent_requests)
            _logger.debug(
                "Semaphore initialized with limit: %d", max_concurrent_requests
            )

        self._setup_ssl_retry_args()
        self.__class__._instances.add(self)

    def _setup_ssl_retry_args(self) -> None:
        original_retry = self.retry_args.get(
            "retry", retry_if_exception(lambda _: False)
        )
        # Type checking assists mypy with static analysis while also providing
        # runtime validation to prevent configuration errors
        if not isinstance(original_retry, retry_if_exception):
            raise TypeError(
                "Retry policy must be of type 'retry_if_exception'"
            )

        def combined_retry(exception: BaseException) -> bool:
            is_ssl = _is_ssl_error(exception)
            if is_ssl:
                self.__class__._register_ssl_error()
            return is_ssl or original_retry.predicate(exception)

        original_before_sleep = self.retry_args.get(
            "before_sleep", lambda _: None
        )

        async def ssl_before_sleep(retry_state: RetryCallState) -> None:
            if retry_state.outcome is None:
                return

            exception = retry_state.outcome.exception()
            if exception and _is_ssl_error(exception):
                _logger.warning(
                    "SSL connection error to %s",
                    str(
                        retry_state.args[0] if retry_state.args else "unknown"
                    ),
                )
                await asyncio.sleep(0.5)

            # Both helps mypy with type checking and serves as a runtime safeguard
            # against non-callable objects being passed as `before_sleep`
            if callable(original_before_sleep):
                await original_before_sleep(
                    retry_state
                ) if iscoroutinefunction(
                    original_before_sleep
                ) else original_before_sleep(retry_state)
                return
            raise ValueError(
                "Expected 'before_sleep' to be a callable "
                "that accepts a 'RetryCallState' parameter."
            )

        self.retry_args.update(
            retry=retry_if_exception(combined_retry),
            before_sleep=ssl_before_sleep,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        typ: t.Optional[t.Type[BaseException]],
        exc: t.Optional[BaseException],
        tb: t.Optional[TracebackType],
    ) -> None:
        del typ, exc, tb
        await self.aclose()

    def __del__(self) -> None:
        if not self.is_closed:
            self._warn_unclosed_client(asynchronous=True)

    def close(self) -> None:
        """
        This method intentionally raises an error to prevent incorrect usage.
        Async clients should use `aclose()` instead.
        """
        raise TypeError(
            f"Use 'await {self.__class__.__name__}.aclose()' "
            f"instead of '{self.__class__.__name__}.close()'"
        )

    async def aclose(self) -> None:
        if not self.is_closed:
            await self._client.aclose()
            _logger.debug("%s closed", self.__class__.__name__)

    async def request(
        self, method: str, endpoint: EndpointParam, **kwargs: t.Any
    ) -> APIResponse:
        url, headers = self._prepare_request(
            endpoint, kwargs.pop("headers", None)
        )
        await self.__class__._check_connection_recovery()

        async def execute() -> APIResponse:
            assert self.__class__._semaphore is not None  # noqa: S101
            async with self.__class__._semaphore:
                response = await self._client.request(
                    method, url, headers=headers, **kwargs
                )
                result = self.__class__._handle_response(response)

                # Decrease error count on successful request
                if self.__class__._ssl_error_count > 0:
                    with self.__class__._rate_limit_lock:
                        self.__class__._ssl_error_count = max(
                            0, self.__class__._ssl_error_count - 1
                        )

                return result

        retryer = AsyncRetrying(**self.retry_args)
        return await retryer(execute)

    @classmethod
    def _register_ssl_error(cls) -> None:
        current_time = time()
        with cls._rate_limit_lock:
            cls._ssl_error_count += 1
            cls._last_ssl_error_time = current_time
            current_limit = cls._max_concurrent_requests

            if not (
                cls._ssl_error_count >= cls._ssl_error_threshold
                and cls._adaptive_limit_enabled
                and current_limit > cls._min_connections
            ):
                return

            new_limit = max(cls._min_connections, current_limit // 2)
            # fmt: off
            _logger.warning(
                "Adaptive rate limiting: "
                "reducing concurrent connections from %d to %d (SSL errors: %d/%d)",
                current_limit, new_limit, cls._ssl_error_count, cls._ssl_error_threshold,
            )
            # fmt: on

            cls.update_rate_limit(new_limit)
            cls._ssl_error_count = 0

    @classmethod
    async def _check_connection_recovery(cls) -> None:
        current_time = time()
        with cls._rate_limit_lock:
            if (
                current_time - cls._recovery_check_time
                < cls._recovery_interval
                or cls._max_concurrent_requests >= cls._initial_max_requests
            ):
                return

            cls._recovery_check_time = current_time
            time_since_last_error = current_time - cls._last_ssl_error_time
            if time_since_last_error <= cls._recovery_interval:
                return

            current = cls._max_concurrent_requests
            new_limit = min(
                cls._initial_max_requests, current + max(1, current // 2)
            )
            if new_limit <= current:
                return

            # fmt: off
            _logger.info(
                "Connection recovery: increasing concurrent "
                "connections from %d to %d after %.1f minutes of stability",
                current, new_limit, time_since_last_error / 60
            )
            # fmt: on
            cls.update_rate_limit(new_limit)

    @classmethod
    @validate_call
    def _update_initial_max_requests(cls, value: PositiveInt, /) -> None:
        with cls._rate_limit_lock:
            if value > cls._initial_max_requests:
                cls._initial_max_requests = value
                _logger.debug("Updated initial max requests to %d", value)

    @classmethod
    @validate_call
    def update_rate_limit(cls, new_limit: PositiveInt, /) -> None:
        with cls._rate_limit_lock:
            if new_limit > cls.MAX_CONCURRENT_REQUESTS:
                warnings.warn(
                    f"Request limit of {new_limit} exceeds "
                    f"maximum allowed ({cls.MAX_CONCURRENT_REQUESTS})",
                    UserWarning,
                    stacklevel=2,
                )
                new_limit = cls.MAX_CONCURRENT_REQUESTS

            # `cls._semaphore` is None when this method is called from __init__
            if (
                cls._max_concurrent_requests == new_limit
                and cls._semaphore is not None
            ):
                _logger.debug(
                    "Rate limit already set to %d, no change needed", new_limit
                )
                return

            cls._semaphore = asyncio.Semaphore(new_limit)
            cls._max_concurrent_requests = new_limit
            _logger.info(
                "Updated request rate limit to %d concurrent requests",
                new_limit,
            )

    @classmethod
    @validate_call
    def configure_adaptive_limits(
        cls,
        ssl_error_threshold: t.Optional[PositiveInt] = None,
        min_connections: t.Optional[PositiveInt] = None,
        recovery_interval: t.Optional[PositiveInt] = None,
        enabled: t.Optional[bool] = None,
    ) -> None:
        with cls._rate_limit_lock:
            changes_made = False

            if (
                ssl_error_threshold is not None
                and ssl_error_threshold != cls._ssl_error_threshold
            ):
                cls._ssl_error_threshold, changes_made = (
                    ssl_error_threshold,
                    True,
                )

            if (
                min_connections is not None
                and min_connections != cls._min_connections
            ):
                cls._min_connections, changes_made = min_connections, True

            if (
                recovery_interval is not None
                and recovery_interval != cls._recovery_interval
            ):
                cls._recovery_interval, changes_made = recovery_interval, True

            if enabled is not None and enabled != cls._adaptive_limit_enabled:
                cls._adaptive_limit_enabled, changes_made = enabled, True

            # fmt: off
            if not changes_made:
                if any(param is not None for param in (
                    ssl_error_threshold, min_connections,
                    recovery_interval, enabled,
                )):
                    _logger.warning(
                        "No changes made to adaptive limits. "
                        "Current settings: threshold=%d, min_connections=%d, "
                        "enabled=%s, recovery_interval=%d",
                        cls._ssl_error_threshold, cls._min_connections,
                        cls._adaptive_limit_enabled, cls._recovery_interval,
                    )
                return

            _logger.info(
                "Adaptive limits configured: "
                "threshold=%d, min_connections=%d, "
                "enabled=%s, recovery_interval=%d",
                cls._ssl_error_threshold, cls._min_connections,
                cls._adaptive_limit_enabled, cls._recovery_interval,
            )
            # fmt: on


# NOTE: The base client classes are fully functional and could be used directly,
# but the public classes (`SyncClient`, `AsyncClient`) provide additional convenience
# methods that align with FACEIT API's expected HTTP methods.
# This separation allows for a cleaner interface while
# maintaining the core implementation details in the base classes


def _clean_type_hints(kwargs: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    for key in ("expect_item", "expect_page"):
        kwargs.pop(key, None)
    return kwargs


@t.final
class SyncClient(_BaseSyncClient):
    __slots__ = ()

    @t.overload
    def get(
        self,
        endpoint: EndpointParam,
        *,
        expect_item: t.Literal[True],
        **kwargs: t.Any,
    ) -> RawAPIItem: ...

    @t.overload
    def get(
        self,
        endpoint: EndpointParam,
        *,
        expect_page: t.Literal[True],
        **kwargs: t.Any,
    ) -> RawAPIPageResponse: ...

    @t.overload
    def get(self, endpoint: EndpointParam, **kwargs: t.Any) -> APIResponse: ...

    def get(self, endpoint: EndpointParam, **kwargs: t.Any) -> APIResponse:
        return self.request(
            SupportedMethod.GET, endpoint, **_clean_type_hints(kwargs)
        )

    @t.overload
    def post(
        self,
        endpoint: EndpointParam,
        *,
        expect_item: t.Literal[True],
        **kwargs: t.Any,
    ) -> RawAPIItem: ...

    @t.overload
    def post(
        self,
        endpoint: EndpointParam,
        *,
        expect_page: t.Literal[True],
        **kwargs: t.Any,
    ) -> RawAPIPageResponse: ...

    @t.overload
    def post(
        self, endpoint: EndpointParam, **kwargs: t.Any
    ) -> APIResponse: ...

    def post(self, endpoint: EndpointParam, **kwargs: t.Any) -> APIResponse:
        return self.request(
            SupportedMethod.POST, endpoint, **_clean_type_hints(kwargs)
        )


@t.final
class AsyncClient(_BaseAsyncClient):
    __slots__ = ()

    @t.overload
    async def get(
        self,
        endpoint: EndpointParam,
        *,
        expect_item: t.Literal[True],
        **kwargs: t.Any,
    ) -> RawAPIItem: ...

    @t.overload
    async def get(
        self,
        endpoint: EndpointParam,
        *,
        expect_page: t.Literal[True],
        **kwargs: t.Any,
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def get(
        self, endpoint: EndpointParam, **kwargs: t.Any
    ) -> APIResponse: ...

    async def get(
        self, endpoint: EndpointParam, **kwargs: t.Any
    ) -> APIResponse:
        return await self.request(
            SupportedMethod.GET, endpoint, **_clean_type_hints(kwargs)
        )

    @t.overload
    async def post(
        self,
        endpoint: EndpointParam,
        *,
        expect_item: t.Literal[True],
        **kwargs: t.Any,
    ) -> RawAPIItem: ...

    @t.overload
    async def post(
        self,
        endpoint: EndpointParam,
        *,
        expect_page: t.Literal[True],
        **kwargs: t.Any,
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def post(
        self, endpoint: EndpointParam, **kwargs: t.Any
    ) -> APIResponse: ...

    async def post(
        self, endpoint: EndpointParam, **kwargs: t.Any
    ) -> APIResponse:
        return await self.request(
            SupportedMethod.POST, endpoint, **_clean_type_hints(kwargs)
        )
