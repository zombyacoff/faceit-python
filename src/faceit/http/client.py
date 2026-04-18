from __future__ import annotations

import asyncio
import logging
import typing
import warnings
from abc import ABC
from collections import UserString
from functools import lru_cache
from threading import Lock
from time import time
from types import MappingProxyType
from weakref import WeakSet

import httpx
import tenacity
import tenacity.asyncio
from pydantic import PositiveInt, validate_call
from typing_extensions import Never, Self

from faceit.constants import BASE_WIKI_URL
from faceit.exceptions import APIError, DecoupleMissingError, MissingAuthTokenError
from faceit.utils import (
    StrEnum,
    create_uuid_validator,
    invoke_callable,
    locked,
    representation,
)

from .helpers import (
    Endpoint,
    RetryArgs,
    SupportedMethod,
    SupportsExceptionPredicate,
    is_retryable_status,
    is_ssl_error,
)

try:
    import decouple  # pyright: ignore[reportMissingImports]
except ImportError:
    ENV_EXTRA_INSTALLED: typing.Final = False
else:
    ENV_EXTRA_INSTALLED: typing.Final = True  # type: ignore[misc]

if typing.TYPE_CHECKING:
    from faceit.types import (
        EndpointParam,
        RawAPIItem,
        RawAPIPageResponse,
        RawAPIResponse,
        ValidUUID,
    )

_logger = logging.getLogger(__name__)

_HttpxClientT = typing.TypeVar("_HttpxClientT", httpx.Client, httpx.AsyncClient)
_RetryerT = typing.TypeVar("_RetryerT", tenacity.Retrying, tenacity.AsyncRetrying)


class MaxConcurrentRequests(StrEnum):
    ABSOLUTE = "max"


# TODO: The HTTP client is currently designed exclusively for API key authentication,
# which is required for the Data resource. This should be revisited when adding
# support for other resources, as they may require different authentication methods.
@representation("api_key", "base_url", "retry_args")
class BaseAPIClient(ABC, typing.Generic[_HttpxClientT, _RetryerT]):
    __slots__ = (
        "_api_key",
        "_build_endpoint",
        "_retry_args",
        "base_url",
    )

    @typing.final
    class env(UserString):
        """String subclass representing a key to fetch from environment variables."""

        __slots__ = ()

    DEFAULT_API_KEY_ENV: typing.ClassVar = env("FACEIT_SECRET")
    DEFAULT_BASE_URL: typing.ClassVar = "https://open.faceit.com/data/v4"
    DEFAULT_TIMEOUT: typing.ClassVar = 10.0
    DEFAULT_RETRY_ARGS: typing.ClassVar = RetryArgs(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_random_exponential(1, 10),
        retry=tenacity.retry_if_exception(
            lambda e: (
                isinstance(
                    e,
                    (
                        httpx.TimeoutException,
                        httpx.ConnectError,
                        httpx.RemoteProtocolError,
                    ),
                )
                or (isinstance(e, APIError) and is_retryable_status(e.status_code))
            )
        ),
        reraise=True,
        before_sleep=lambda s: _logger.warning(
            "Retry attempt %d failed; sleeping for %.2f seconds before next attempt",
            s.attempt_number,
            0 if s.next_action is None else s.next_action.sleep,
        ),
    )

    if typing.TYPE_CHECKING:
        _retry_args: RetryArgs
        _client: _HttpxClientT
        _retryer: _RetryerT

    __api_key_validator: typing.ClassVar[typing.Callable[[ValidUUID], str]] = (
        create_uuid_validator(
            "Invalid FACEIT API key format: {value!r}. "
            "Please visit the official wiki for API key information: "
            f"{BASE_WIKI_URL}/getting-started/authentication/api-keys"
        )
    )

    def __init__(
        self,
        api_key: typing.Union[ValidUUID, env] = DEFAULT_API_KEY_ENV,
        base_url: str = DEFAULT_BASE_URL,
        retry_args: typing.Optional[RetryArgs] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._api_key_setter(api_key)
        self._retry_args_setter(retry_args or RetryArgs())
        self._build_endpoint = lru_cache(self._build_endpoint_unwrapped)

    @property
    def api_key(self) -> str:
        return self._api_key[:4] + "..." + self._api_key[-4:]

    @api_key.setter
    def api_key(self, value: typing.Union[ValidUUID, env]) -> None:
        self._api_key_setter(value)

    @property
    def retry_args(self) -> RetryArgs:
        return self._retry_args

    @retry_args.setter
    def retry_args(self, value: RetryArgs) -> None:
        self._retry_args_setter(value)

    # Provide read-only access to the underlying client for
    # exceptional cases where direct interaction might be necessary,
    # while keeping the interface immutable
    @property
    def raw_client(self) -> _HttpxClientT:
        return self._client

    @property
    def is_closed(self) -> bool:
        return self._client.is_closed if hasattr(self, "_client") else True

    @property
    def _base_headers(self) -> typing.Mapping[str, str]:
        return MappingProxyType({
            "Accept": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        })

    def create_endpoint(self, *path_parts: str) -> Endpoint:
        return Endpoint(*path_parts, base=self.base_url)

    def _api_key_setter(self, value: typing.Union[ValidUUID, env], /) -> None:
        self._api_key = self.__class__.__api_key_validator(
            self.__class__._get_secret_from_env(str(value))
            if isinstance(value, self.__class__.env)
            else value
        )

    def _retry_args_setter(self, retry_args: RetryArgs, /) -> None:
        if not isinstance(retry_args, dict):
            raise TypeError(f"Expected RetryArgs, got {type(retry_args).__name__}")
        self._retry_args = {**self.__class__.DEFAULT_RETRY_ARGS, **retry_args}

    def _build_endpoint_unwrapped(self, endpoint: EndpointParam, /) -> str:
        return str(
            endpoint.with_base(self.base_url)
            if isinstance(endpoint, Endpoint)
            else self.create_endpoint(endpoint)
        )

    def _prepare_request(
        self,
        endpoint: EndpointParam,
        headers: typing.Optional[httpx._types.HeaderTypes] = None,
    ) -> typing.Tuple[str, httpx.Headers]:
        combined_headers = httpx.Headers(self._base_headers)
        combined_headers.update(headers)
        return self._build_endpoint(endpoint), combined_headers

    @staticmethod
    def _get_secret_from_env(key: str, /) -> str:
        if not ENV_EXTRA_INSTALLED:
            raise DecoupleMissingError
        try:
            # cast is required because `decouple` is untyped
            return typing.cast("str", decouple.config(key))
        except decouple.UndefinedValueError:
            raise MissingAuthTokenError(key) from None

    @staticmethod
    def _handle_response(response: httpx.Response, /) -> RawAPIResponse:
        try:
            response.raise_for_status()
            _logger.debug("Successful response from %s", response.url)
            return typing.cast("RawAPIResponse", response.json())
        except httpx.HTTPStatusError as e:
            # fmt: off
            if is_retryable_status(e.response.status_code):
                _logger.warning(
                    "Retryable HTTP error %s at %s: %s",
                    e.response.status_code, e.response.url, e.response.text
                )
            else:
                _logger.exception(
                    "HTTP error %s at %s: %s",
                    response.status_code, response.url, response.text,
                )
            raise APIError.from_response(response) from e
            # fmt: on
        except (ValueError, httpx.DecodingError):
            _logger.exception(
                "Invalid JSON response from %s: %s", response.url, response.text
            )
            raise APIError(response, message="Invalid JSON response") from None


class _BaseSyncClient(BaseAPIClient[httpx.Client, tenacity.Retrying]):
    __slots__ = ("_client", "_retryer")

    def __init__(
        self,
        api_key: typing.Union[
            ValidUUID, BaseAPIClient.env
        ] = BaseAPIClient.DEFAULT_API_KEY_ENV,
        *,
        base_url: str = BaseAPIClient.DEFAULT_BASE_URL,
        timeout: float = BaseAPIClient.DEFAULT_TIMEOUT,
        retry_args: typing.Optional[RetryArgs] = None,
        **raw_client_kwargs: typing.Any,
    ) -> None:
        super().__init__(api_key, base_url, retry_args)
        self._client = httpx.Client(
            timeout=timeout, headers=self._base_headers, **raw_client_kwargs
        )
        self._retryer = tenacity.Retrying(**self._retry_args)  # type: ignore[arg-type]

    def close(self) -> None:
        if not self.is_closed:
            self._client.close()
            _logger.debug("%s closed", self.__class__.__name__)

    def request(
        self, method: str, endpoint: EndpointParam, **kwargs: typing.Any
    ) -> RawAPIResponse:
        url, headers = self._prepare_request(endpoint, kwargs.pop("headers", None))
        return self._retryer(
            lambda: self.__class__._handle_response(
                self._client.request(method, url, headers=headers, **kwargs)
            )
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object, **__: object) -> None:
        self.close()


# NOTE: Logic on eliminating SSL errors was added because during tests
# it was found that such errors often pop up even with a small
# number of concurrent requests, probably problems on the FACEIT API side
class _BaseAsyncClient(BaseAPIClient[httpx.AsyncClient, tenacity.AsyncRetrying]):
    __slots__ = ("__weakref__", "_client", "_retryer")

    _instances: typing.ClassVar[WeakSet[_BaseAsyncClient]] = WeakSet()

    _lock: typing.ClassVar = Lock()
    _asyncio_lock: typing.ClassVar = asyncio.Lock()
    _semaphore: typing.ClassVar[typing.Optional[asyncio.Semaphore]] = None
    _ssl_error_count: typing.ClassVar = 0
    _adaptive_limit_enabled: typing.ClassVar = True
    _last_ssl_error_time: typing.ClassVar = time()
    _recovery_check_time: typing.ClassVar = 0.0

    # Current limit value is based on empirical testing,
    # but requires further investigation for optimal setting
    MAX_CONCURRENT_REQUESTS_ABSOLUTE: typing.ClassVar = 100

    DEFAULT_MAX_CONCURRENT_REQUESTS: typing.ClassVar = 30
    DEFAULT_SSL_ERROR_THRESHOLD: typing.ClassVar = 5
    DEFAULT_MIN_CONNECTIONS: typing.ClassVar = 5
    DEFAULT_RECOVERY_INTERVAL: typing.ClassVar = 300

    _initial_max_requests: typing.ClassVar = DEFAULT_MAX_CONCURRENT_REQUESTS
    _max_concurrent_requests: typing.ClassVar = DEFAULT_MAX_CONCURRENT_REQUESTS
    _ssl_error_threshold: typing.ClassVar = DEFAULT_SSL_ERROR_THRESHOLD
    _min_connections: typing.ClassVar = DEFAULT_MIN_CONNECTIONS
    _recovery_interval: typing.ClassVar = DEFAULT_RECOVERY_INTERVAL

    DEFAULT_KEEPALIVE_EXPIRY: typing.ClassVar = 30.0

    def __init__(
        self,
        api_key: typing.Union[
            ValidUUID, BaseAPIClient.env
        ] = BaseAPIClient.DEFAULT_API_KEY_ENV,
        *,
        base_url: str = BaseAPIClient.DEFAULT_BASE_URL,
        timeout: float = BaseAPIClient.DEFAULT_TIMEOUT,
        retry_args: typing.Optional[RetryArgs] = None,
        max_concurrent_requests: typing.Union[
            MaxConcurrentRequests, int
        ] = DEFAULT_MAX_CONCURRENT_REQUESTS,
        ssl_error_threshold: int = DEFAULT_SSL_ERROR_THRESHOLD,
        min_connections: int = DEFAULT_MIN_CONNECTIONS,
        recovery_interval: int = DEFAULT_RECOVERY_INTERVAL,
        **raw_client_kwargs: typing.Any,
    ) -> None:
        super().__init__(api_key, base_url, retry_args)
        max_concurrent_requests = self.__class__._update_initial_max_requests(
            max_concurrent_requests
        )

        if (
            ssl_error_threshold != self.__class__.DEFAULT_SSL_ERROR_THRESHOLD
            or min_connections != self.__class__.DEFAULT_MIN_CONNECTIONS
            or recovery_interval != self.__class__.DEFAULT_RECOVERY_INTERVAL
        ):
            self.__class__.configure_adaptive_limits(
                ssl_error_threshold, min_connections, recovery_interval
            )

        limits = raw_client_kwargs.pop("limits", None) or httpx.Limits(
            max_keepalive_connections=max_concurrent_requests,
            max_connections=max_concurrent_requests * 2,
            keepalive_expiry=self.__class__.DEFAULT_KEEPALIVE_EXPIRY,
        )
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=self._base_headers,
            limits=limits,
            **raw_client_kwargs,
        )
        self._retryer = tenacity.AsyncRetrying(**self._retry_args)  # type: ignore[arg-type]

        # Initialize or update the semaphore if needed
        if (
            self.__class__._semaphore is None
            or max_concurrent_requests != self.__class__._max_concurrent_requests
        ):
            self.__class__.update_rate_limit(max_concurrent_requests)
            _logger.debug(
                "Semaphore initialized with limit: %d", max_concurrent_requests
            )

        self._setup_ssl_retry_args()
        self.__class__._instances.add(self)

    def _setup_ssl_retry_args(self) -> None:
        original_retry = self._retry_args.get("retry", lambda _: False)

        async def combined_retry(exception: BaseException) -> bool:
            if is_ssl_error(exception):
                return self.__class__._register_ssl_error()
            if isinstance(original_retry, SupportsExceptionPredicate):
                return await invoke_callable(original_retry.predicate, exception)  # type: ignore[unreachable]
            return await invoke_callable(original_retry, exception)

        original_before_sleep = self._retry_args.get("before_sleep", None) or (
            lambda _: None
        )

        async def ssl_before_sleep(retry_state: tenacity.RetryCallState) -> None:
            if retry_state.outcome is None:
                return

            exception = retry_state.outcome.exception()
            if exception is not None and is_ssl_error(exception):
                _logger.warning(
                    "SSL connection error to %s",
                    retry_state.args[0] if retry_state.args else "unknown",
                )
                await asyncio.sleep(0.5)

            await invoke_callable(original_before_sleep, retry_state)

        self._retry_args.update({
            "retry": tenacity.asyncio.retry_if_exception(combined_retry),
            "before_sleep": ssl_before_sleep,
        })

    async def aclose(self) -> None:
        if not self.is_closed:
            await self._client.aclose()
            _logger.debug("%s closed", self.__class__.__name__)

    async def request(
        self, method: str, endpoint: EndpointParam, **kwargs: typing.Any
    ) -> RawAPIResponse:
        url, headers = self._prepare_request(endpoint, kwargs.pop("headers", None))
        await self.__class__._check_connection_recovery()

        async def execute() -> RawAPIResponse:
            assert self.__class__._semaphore is not None
            async with self.__class__._semaphore:
                result = self.__class__._handle_response(
                    await self._client.request(method, url, headers=headers, **kwargs)
                )

                # Decrease error count on successful request
                if self.__class__._ssl_error_count > 0:
                    with self.__class__._lock:
                        self.__class__._ssl_error_count = max(
                            0, self.__class__._ssl_error_count - 1
                        )

                return result

        return await self._retryer(execute)

    @classmethod
    @locked(_lock)
    def _register_ssl_error(
        cls,
        # Always returns `True` to ensure retry
        # happens for SSL errors in the retry mechanism
    ) -> typing.Literal[True]:
        cls._ssl_error_count += 1
        cls._last_ssl_error_time = time()
        current_limit = cls._max_concurrent_requests

        if not (
            cls._ssl_error_count >= cls._ssl_error_threshold
            and cls._adaptive_limit_enabled
            and current_limit > cls._min_connections
        ):
            return True

        new_limit = max(cls._min_connections, current_limit // 2)
        # fmt: off
        _logger.warning(
            "Adaptive rate limiting: "
            "reducing concurrent connections "
            "from %d to %d (SSL errors: %d/%d)",
            current_limit, new_limit,
            cls._ssl_error_count, cls._ssl_error_threshold,
        )
        # fmt: on

        cls.update_rate_limit(new_limit)
        cls._ssl_error_count = 0
        return True

    @classmethod
    @locked(_asyncio_lock)
    async def _check_connection_recovery(cls) -> None:
        current_time = time()
        if (
            current_time - cls._recovery_check_time < cls._recovery_interval
            or cls._max_concurrent_requests >= cls._initial_max_requests
        ):
            return

        cls._recovery_check_time = current_time
        time_since_last_error = current_time - cls._last_ssl_error_time
        if time_since_last_error <= cls._recovery_interval:
            return

        current = cls._max_concurrent_requests
        new_limit = min(cls._initial_max_requests, current + max(1, current // 2))
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
    @locked(_lock)
    @validate_call
    def _update_initial_max_requests(
        cls, value: typing.Union[MaxConcurrentRequests, PositiveInt], /
    ) -> int:
        max_concurrent_requests = (
            cls.MAX_CONCURRENT_REQUESTS_ABSOLUTE
            if value == MaxConcurrentRequests.ABSOLUTE
            else value
        )
        if max_concurrent_requests > cls._initial_max_requests:
            cls._initial_max_requests = max_concurrent_requests
            _logger.debug("Updated initial max requests to %d", max_concurrent_requests)
        return max_concurrent_requests

    @classmethod
    def close(cls) -> Never:
        """
        This method intentionally raises an error to prevent incorrect usage.

        Async clients should use ``aclose()`` instead.
        """
        raise RuntimeError(
            f"Use 'await {cls.__name__}.aclose()' instead of '{cls.__name__}.close()'."
        )

    @classmethod
    async def close_all(cls) -> None:
        if cls._instances:
            await asyncio.gather(*(client.aclose() for client in cls._instances))

    @classmethod
    @locked(_lock)
    @validate_call
    def update_rate_limit(cls, new_limit: PositiveInt, /) -> None:
        if new_limit > cls.MAX_CONCURRENT_REQUESTS_ABSOLUTE:
            warnings.warn(
                f"Request limit of {new_limit} exceeds "
                f"maximum allowed ({cls.MAX_CONCURRENT_REQUESTS_ABSOLUTE})",
                UserWarning,
                stacklevel=4,
            )
            new_limit = cls.MAX_CONCURRENT_REQUESTS_ABSOLUTE

        # `cls._semaphore` is None when this method is called from `__init__`
        if cls._max_concurrent_requests == new_limit and cls._semaphore is not None:
            _logger.debug("Rate limit already set to %d, no change needed", new_limit)
            return

        cls._semaphore = asyncio.Semaphore(new_limit)
        cls._max_concurrent_requests = new_limit
        _logger.info("Updated request rate limit to %d concurrent requests", new_limit)

    @classmethod
    @locked(_lock)
    @validate_call
    def configure_adaptive_limits(
        cls,
        ssl_error_threshold: typing.Optional[PositiveInt] = None,
        min_connections: typing.Optional[PositiveInt] = None,
        recovery_interval: typing.Optional[PositiveInt] = None,
        enabled: typing.Optional[bool] = None,
    ) -> None:
        params = {
            "ssl_error_threshold": ("_ssl_error_threshold", ssl_error_threshold),
            "min_connections": ("_min_connections", min_connections),
            "recovery_interval": ("_recovery_interval", recovery_interval),
            "adaptive_limit_enabled": ("_adaptive_limit_enabled", enabled),
        }

        changes_made = False

        for attr, value in params.values():
            if value is not None and value != getattr(cls, attr):
                setattr(cls, attr, value)
                changes_made = True

        if changes_made:
            _logger.info(
                "Adaptive limits configured: threshold=%d, min_connections=%d, "
                "enabled=%s, recovery_interval=%d",
                cls._ssl_error_threshold,
                cls._min_connections,
                cls._adaptive_limit_enabled,
                cls._recovery_interval,
            )
            return

        if any(value is not None for _, value in params.values()):
            _logger.warning(
                "No changes made to adaptive limits. "
                "Current settings: threshold=%d, min_connections=%d, "
                "enabled=%s, recovery_interval=%d",
                cls._ssl_error_threshold,
                cls._min_connections,
                cls._adaptive_limit_enabled,
                cls._recovery_interval,
            )

    def __enter__(self) -> Never:
        raise RuntimeError("Use 'async with' instead.")

    def __exit__(self, *_: object, **__: object) -> None:
        pass

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object, **__: object) -> None:
        await self.aclose()


# NOTE: The base client classes are fully functional and could be used
# directly, but the public classes (`SyncClient`, `AsyncClient`) provide
# additional convenience methods that align with FACEIT API's expected HTTP
# methods. This separation allows for a cleaner interface while maintaining
# the core implementation details in the base classes


# fmt: off
_TYPE_HINT_KEYS: typing.Final = {"expect_item", "expect_page"}
def _clean_type_hints(  # noqa: E302
    kwargs: typing.Dict[str, typing.Any], /
) -> typing.Dict[str, typing.Any]:
    for key in _TYPE_HINT_KEYS:
        kwargs.pop(key, None)
    return kwargs
# fmt: on


@typing.final
class SyncClient(_BaseSyncClient):
    __slots__ = ()

    @typing.overload
    def get(
        self,
        endpoint: EndpointParam,
        *,
        expect_item: typing.Literal[True],
        **kwargs: typing.Any,
    ) -> RawAPIItem: ...

    @typing.overload
    def get(
        self,
        endpoint: EndpointParam,
        *,
        expect_page: typing.Literal[True],
        **kwargs: typing.Any,
    ) -> RawAPIPageResponse: ...

    @typing.overload
    def get(self, endpoint: EndpointParam, **kwargs: typing.Any) -> RawAPIResponse: ...

    def get(self, endpoint: EndpointParam, **kwargs: typing.Any) -> RawAPIResponse:
        return self.request(SupportedMethod.GET, endpoint, **_clean_type_hints(kwargs))

    @typing.overload
    def post(
        self,
        endpoint: EndpointParam,
        *,
        expect_item: typing.Literal[True],
        **kwargs: typing.Any,
    ) -> RawAPIItem: ...

    @typing.overload
    def post(
        self,
        endpoint: EndpointParam,
        *,
        expect_page: typing.Literal[True],
        **kwargs: typing.Any,
    ) -> RawAPIPageResponse: ...

    @typing.overload
    def post(self, endpoint: EndpointParam, **kwargs: typing.Any) -> RawAPIResponse: ...

    def post(self, endpoint: EndpointParam, **kwargs: typing.Any) -> RawAPIResponse:
        return self.request(SupportedMethod.POST, endpoint, **_clean_type_hints(kwargs))


@typing.final
class AsyncClient(_BaseAsyncClient):
    __slots__ = ()

    @typing.overload
    async def get(
        self,
        endpoint: EndpointParam,
        *,
        expect_item: typing.Literal[True],
        **kwargs: typing.Any,
    ) -> RawAPIItem: ...

    @typing.overload
    async def get(
        self,
        endpoint: EndpointParam,
        *,
        expect_page: typing.Literal[True],
        **kwargs: typing.Any,
    ) -> RawAPIPageResponse: ...

    @typing.overload
    async def get(
        self, endpoint: EndpointParam, **kwargs: typing.Any
    ) -> RawAPIResponse: ...

    async def get(
        self, endpoint: EndpointParam, **kwargs: typing.Any
    ) -> RawAPIResponse:
        return await self.request(
            SupportedMethod.GET, endpoint, **_clean_type_hints(kwargs)
        )

    @typing.overload
    async def post(
        self,
        endpoint: EndpointParam,
        *,
        expect_item: typing.Literal[True],
        **kwargs: typing.Any,
    ) -> RawAPIItem: ...

    @typing.overload
    async def post(
        self,
        endpoint: EndpointParam,
        *,
        expect_page: typing.Literal[True],
        **kwargs: typing.Any,
    ) -> RawAPIPageResponse: ...

    @typing.overload
    async def post(
        self, endpoint: EndpointParam, **kwargs: typing.Any
    ) -> RawAPIResponse: ...

    async def post(
        self, endpoint: EndpointParam, **kwargs: typing.Any
    ) -> RawAPIResponse:
        return await self.request(
            SupportedMethod.POST, endpoint, **_clean_type_hints(kwargs)
        )
