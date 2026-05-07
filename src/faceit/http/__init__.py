from typing_extensions import deprecated

from .client import AsyncClient, MaxConcurrentRequests, SyncClient
from .helpers import Endpoint, RetryArgs, SupportedMethod

__all__ = [
    "AsyncClient",
    "Endpoint",
    "FromEnv",
    "MaxConcurrentRequests",
    "RetryArgs",
    "SupportedMethod",
    "SyncClient",
]

FromEnv = SyncClient.env


@deprecated(
    "`EnvKey` is deprecated and will be removed in a future version. Use `FromEnv` instead."
)
class EnvKey(SyncClient.env):  # type: ignore[misc] # pyright: ignore[reportGeneralTypeIssues]
    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def] # noqa: ANN002, ANN003, ANN204
        import warnings  # noqa: PLC0415

        warnings.warn(
            "`EnvKey` is deprecated and will be removed in a future version. Use `FromEnv` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
