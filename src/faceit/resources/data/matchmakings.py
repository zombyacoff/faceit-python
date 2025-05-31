from __future__ import annotations

import typing
from abc import ABC

from pydantic import AfterValidator, validate_call
from typing_extensions import Annotated, TypeAlias

from faceit.http import AsyncClient, SyncClient
from faceit.resources.base import BaseResource, FaceitResourcePath, ModelPlaceholder
from faceit.types import (
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIItem,
    ValidUUID,
)

_MatchmakingID: TypeAlias = ValidUUID
_MatchmakingIDValidated: TypeAlias = Annotated[
    _MatchmakingID, AfterValidator(str)  # TODO: Validation function
]


class BaseMatchmakings(
    BaseResource[ClientT],
    ABC,
    resource_path=FaceitResourcePath.MATCHMAKINGS,
):
    __slots__ = ()


class SyncMatchmakings(
    BaseMatchmakings[SyncClient], typing.Generic[APIResponseFormatT]
):
    __slots__ = ()

    @typing.overload
    def get(
        self: SyncMatchmakings[Raw], matchmaking_id: _MatchmakingID
    ) -> RawAPIItem: ...

    @typing.overload
    def get(
        self: SyncMatchmakings[Model], matchmaking_id: _MatchmakingID
    ) -> ModelNotImplemented: ...

    @validate_call
    def get(
        self, matchmaking_id: _MatchmakingIDValidated
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(matchmaking_id), expect_item=True
            ),
            ModelPlaceholder,
        )

    __call__ = get


class AsyncMatchmakings(
    BaseMatchmakings[AsyncClient], typing.Generic[APIResponseFormatT]
):
    __slots__ = ()

    @typing.overload
    async def get(
        self: AsyncMatchmakings[Raw], matchmaking_id: _MatchmakingID
    ) -> RawAPIItem: ...

    @typing.overload
    async def get(
        self: AsyncMatchmakings[Model], matchmaking_id: _MatchmakingID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def get(
        self, matchmaking_id: _MatchmakingIDValidated
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(matchmaking_id), expect_item=True
            ),
            ModelPlaceholder,
        )

    __call__ = get
