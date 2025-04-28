from __future__ import annotations

import typing as t
from abc import ABC

import typing_extensions as te
from pydantic import AfterValidator, validate_call

from faceit.http import AsyncClient, SyncClient
from faceit.resources.base import (
    BaseResource,
    FaceitResourcePath,
    ModelPlaceholder,
)
from faceit.types import (
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIItem,
    ValidUUID,
)

_MatchmakingID: te.TypeAlias = ValidUUID
_MatchmakingIDValidator: te.TypeAlias = te.Annotated[
    _MatchmakingID, AfterValidator(str)  # TODO: Validation function
]


class BaseMatchmakings(
    BaseResource[ClientT],
    ABC,
    resource_path=FaceitResourcePath.MATCHMAKINGS,
):
    __slots__ = ()


class SyncMatchmakings(
    BaseMatchmakings[SyncClient], t.Generic[APIResponseFormatT]
):
    __slots__ = ()

    @t.overload
    def get(
        self: SyncMatchmakings[Raw], matchmaking_id: _MatchmakingID
    ) -> RawAPIItem: ...

    @t.overload
    def get(
        self: SyncMatchmakings[Model], matchmaking_id: _MatchmakingID
    ) -> ModelNotImplemented: ...

    @validate_call
    def get(
        self, matchmaking_id: _MatchmakingIDValidator
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(matchmaking_id), expect_item=True
            ),
            ModelPlaceholder,
        )

    __call__ = get


class AsyncMatchmakings(
    BaseMatchmakings[AsyncClient], t.Generic[APIResponseFormatT]
):
    __slots__ = ()

    @t.overload
    async def get(
        self: AsyncMatchmakings[Raw], matchmaking_id: _MatchmakingID
    ) -> RawAPIItem: ...

    @t.overload
    async def get(
        self: AsyncMatchmakings[Model], matchmaking_id: _MatchmakingID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def get(
        self, matchmaking_id: _MatchmakingIDValidator
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(matchmaking_id), expect_item=True
            ),
            ModelPlaceholder,
        )

    __call__ = get
