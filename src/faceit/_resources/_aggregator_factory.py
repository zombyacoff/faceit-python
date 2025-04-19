import typing as t
from abc import ABC
from dataclasses import dataclass
from functools import cached_property

from faceit._typing import ClientT

from ._base import BaseResource

_RT = t.TypeVar("_RT", bound=BaseResource)
_AT = t.TypeVar("_AT", bound="BaseResources")


@dataclass(eq=False, frozen=True)
class BaseResources(t.Generic[ClientT], ABC):
    _client: ClientT


def _add_resource_property(
    cls: t.Type[_AT], resource_cls: t.Type[_RT], path: str, *, raw: bool
) -> None:
    prop = cached_property(lambda self: resource_cls(self._client, raw=raw))
    setattr(cls, path, prop)
    if hasattr(prop, "__set_name__"):
        prop.__set_name__(cls, path)


def resource_aggregator(
    *resource_classes: t.Type[_RT],
) -> t.Callable[[t.Type[_AT]], t.Type[_AT]]:
    def decorator(cls: t.Type[_AT]) -> t.Type[_AT]:
        for resource_cls in resource_classes:
            _add_resource_property(
                cls, resource_cls, f"raw_{resource_cls._RAW_PATH}", raw=True
            )
            _add_resource_property(
                cls, resource_cls, resource_cls._RAW_PATH, raw=False
            )
        return cls

    return decorator
