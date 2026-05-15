from __future__ import annotations

from abc import ABC
from typing import Annotated, Generic, TypeAlias, final, overload

from pydantic import AfterValidator, validate_call

from faceit.api.base import BaseResource, ModelPlaceholder
from faceit.http import AsyncClient, SyncClient
from faceit.models.custom_types import FaceitMatchID
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
    resource_path="matches",
):
    __slots__ = ()


@final
class SyncMatches(BaseMatches[SyncClient], Generic[APIResponseFormatT]):
    __slots__ = ()

    @overload
    def get(self: SyncMatches[Raw], match_id: _MatchID) -> RawAPIItem: ...

    @overload
    def get(self: SyncMatches[Model], match_id: _MatchID) -> ModelNotImplemented: ...

    @validate_call
    def get(self, match_id: _MatchIDValidated) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            self._client.get(self.__class__.PATH / match_id, expect_item=True),
            ModelPlaceholder,
        )

    __call__ = get

    @overload
    def stats(self: SyncMatches[Raw], match_id: _MatchID) -> RawAPIItem: ...

    @overload
    def stats(self: SyncMatches[Model], match_id: _MatchID) -> ModelNotImplemented: ...

    @validate_call
    def stats(self, match_id: _MatchIDValidated) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / match_id / "stats", expect_item=True
            ),
            ModelPlaceholder,
        )


@final
class AsyncMatches(BaseMatches[AsyncClient], Generic[APIResponseFormatT]):
    __slots__ = ()

    @overload
    async def get(self: AsyncMatches[Raw], match_id: _MatchID) -> RawAPIItem: ...

    @overload
    async def get(
        self: AsyncMatches[Model], match_id: _MatchID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def get(
        self, match_id: _MatchIDValidated
    ) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            await self._client.get(self.__class__.PATH / match_id, expect_item=True),
            ModelPlaceholder,
        )

    __call__ = get

    @overload
    async def stats(self: AsyncMatches[Raw], match_id: _MatchID) -> RawAPIItem: ...

    @overload
    async def stats(
        self: AsyncMatches[Model], match_id: _MatchID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def stats(
        self, match_id: _MatchIDValidated
    ) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / match_id / "stats", expect_item=True
            ),
            ModelPlaceholder,
        )
