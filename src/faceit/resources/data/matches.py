from __future__ import annotations

import typing
from abc import ABC

from pydantic import AfterValidator, validate_call
from typing_extensions import Annotated, TypeAlias, deprecated

from faceit.http import AsyncClient, SyncClient
from faceit.models.custom_types import FaceitMatchID
from faceit.resources.base import BaseResource, FaceitResourcePath, ModelPlaceholder
from faceit.types import (
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIItem,
)

_MatchID: TypeAlias = str
# We use `AfterValidator` with the `_MatchID` type alias instead of `FaceitMatchID` directly
# to avoid mypy complaints. Mypy cannot fully recognize our custom type as compatible
# with str, so this approach ensures proper type checking and validation.
_MatchIDValidated: TypeAlias = Annotated[
    _MatchID, AfterValidator(FaceitMatchID._validate)
]


class BaseMatches(
    BaseResource[ClientT],
    ABC,
    resource_path=FaceitResourcePath.MATCHES,
):
    __slots__ = ()


class SyncMatches(BaseMatches[SyncClient], typing.Generic[APIResponseFormatT]):
    __slots__ = ()

    @typing.overload
    def get(self: SyncMatches[Raw], match_id: _MatchID) -> RawAPIItem: ...

    @typing.overload
    def get(self: SyncMatches[Model], match_id: _MatchID) -> ModelNotImplemented: ...

    @validate_call
    def get(
        self, match_id: _MatchIDValidated
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(self.__class__.PATH / match_id, expect_item=True),
            ModelPlaceholder,
        )

    __call__ = get

    @deprecated(
        "`details` is deprecated and will be removed in a future release. Use `get` instead."
    )
    def details(self, match_id: typing.Any) -> typing.Any:
        return self.get(match_id)

    @typing.overload
    def stats(self: SyncMatches[Raw], match_id: _MatchID) -> RawAPIItem: ...

    @typing.overload
    def stats(self: SyncMatches[Model], match_id: _MatchID) -> ModelNotImplemented: ...

    @validate_call
    def stats(
        self, match_id: _MatchIDValidated
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / match_id / "stats", expect_item=True
            ),
            ModelPlaceholder,
        )


class AsyncMatches(BaseMatches[AsyncClient], typing.Generic[APIResponseFormatT]):
    __slots__ = ()

    @typing.overload
    async def get(self: AsyncMatches[Raw], match_id: _MatchID) -> RawAPIItem: ...

    @typing.overload
    async def get(
        self: AsyncMatches[Model], match_id: _MatchID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def get(
        self, match_id: _MatchIDValidated
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(self.__class__.PATH / match_id, expect_item=True),
            ModelPlaceholder,
        )

    __call__ = get

    @deprecated(
        "`details` is deprecated and will be removed in a future release. Use `get` instead."
    )
    async def details(self, match_id: typing.Any) -> typing.Any:
        return await self.get(match_id)

    @typing.overload
    async def stats(self: AsyncMatches[Raw], match_id: _MatchID) -> RawAPIItem: ...

    @typing.overload
    async def stats(
        self: AsyncMatches[Model], match_id: _MatchID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def stats(
        self, match_id: _MatchIDValidated
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / match_id / "stats", expect_item=True
            ),
            ModelPlaceholder,
        )
