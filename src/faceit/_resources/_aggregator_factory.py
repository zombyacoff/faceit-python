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


def resource_aggregator(cls: t.Type[_AT]) -> t.Type[_AT]:
    for name, resource_type in getattr(cls, "__annotations__", {}).items():

        def make_property(
            is_raw: bool,
            resource_type: t.Type[_RT] = resource_type,
        ) -> cached_property:
            return cached_property(
                lambda self: resource_type(self._client, raw=is_raw)
            )

        prop = make_property(name.startswith("raw_"))
        setattr(cls, name, prop)
        if hasattr(prop, "__set_name__"):
            prop.__set_name__(cls, name)

    return cls
