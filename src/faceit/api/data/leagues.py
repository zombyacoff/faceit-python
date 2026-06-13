from __future__ import annotations

from abc import ABC
from typing import Annotated, Generic, TypeAlias, final, overload

from pydantic import AfterValidator, Field, validate_call

from faceit.api.base import BaseResource, ModelPlaceholder
from faceit.http import AsyncClient, SyncClient
from faceit.types import (
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIItem,
    ValidUUID,
)
from faceit.utils import create_uuid_validator

from .players import PlayerID, PlayerIDValidated

_LeagueID: TypeAlias = ValidUUID
_LeagueIDValidated: TypeAlias = Annotated[
    _LeagueID,
    AfterValidator(create_uuid_validator(arg_name="league_id")),
]
_SeasonID: TypeAlias = Annotated[int, Field(ge=1)]


class BaseLeagues(
    BaseResource[ClientT],
    ABC,
    resource_path="leagues",
):
    __slots__ = ()


@final
class SyncLeagues(BaseLeagues[SyncClient], Generic[APIResponseFormatT]):
    __slots__ = ()

    @overload
    def get(self: SyncLeagues[Raw], matchmaking_id: _LeagueID) -> RawAPIItem: ...

    @overload
    def get(
        self: SyncLeagues[Model], matchmaking_id: _LeagueID
    ) -> ModelNotImplemented: ...

    @validate_call
    def get(
        self, matchmaking_id: _LeagueIDValidated
    ) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(matchmaking_id), expect_item=True
            ),
            ModelPlaceholder,
        )

    __call__ = get

    @overload
    def season(
        self: SyncLeagues[Raw], matchmaking_id: _LeagueID, season_id: _SeasonID
    ) -> RawAPIItem: ...

    @overload
    def season(
        self: SyncLeagues[Model], matchmaking_id: _LeagueID, season_id: _SeasonID
    ) -> ModelNotImplemented: ...

    @validate_call
    def season(
        self, matchmaking_id: _LeagueIDValidated, season_id: _SeasonID
    ) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(matchmaking_id) / "seasons" / str(season_id),
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    @overload
    def player(
        self: SyncLeagues[Raw],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
        player_id: PlayerID,
    ) -> RawAPIItem: ...

    @overload
    def player(
        self: SyncLeagues[Model],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
        player_id: PlayerID,
    ) -> ModelNotImplemented: ...

    @validate_call
    def player(
        self,
        matchmaking_id: _LeagueIDValidated,
        season_id: _SeasonID,
        player_id: PlayerIDValidated,
    ) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(matchmaking_id) / "seasons" / str(season_id) / "players" / str(player_id),
                expect_item=True,
            ),
            ModelPlaceholder,
        )  # fmt: skip


@final
class AsyncLeagues(BaseLeagues[AsyncClient], Generic[APIResponseFormatT]):
    __slots__ = ()

    @overload
    async def get(self: AsyncLeagues[Raw], matchmaking_id: _LeagueID) -> RawAPIItem: ...

    @overload
    async def get(
        self: AsyncLeagues[Model], matchmaking_id: _LeagueID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def get(
        self, matchmaking_id: _LeagueIDValidated
    ) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(matchmaking_id), expect_item=True
            ),
            ModelPlaceholder,
        )

    __call__ = get

    @overload
    async def season(
        self: AsyncLeagues[Raw], matchmaking_id: _LeagueID, season_id: _SeasonID
    ) -> RawAPIItem: ...

    @overload
    async def season(
        self: AsyncLeagues[Model], matchmaking_id: _LeagueID, season_id: _SeasonID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def season(
        self, matchmaking_id: _LeagueIDValidated, season_id: _SeasonID
    ) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(matchmaking_id) / "seasons" / str(season_id),
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    @overload
    async def player(
        self: AsyncLeagues[Raw],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
        player_id: PlayerID,
    ) -> RawAPIItem: ...

    @overload
    async def player(
        self: AsyncLeagues[Model],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
        player_id: PlayerID,
    ) -> ModelNotImplemented: ...

    @validate_call
    async def player(
        self,
        matchmaking_id: _LeagueIDValidated,
        season_id: _SeasonID,
        player_id: PlayerIDValidated,
    ) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(matchmaking_id) / "seasons" / str(season_id) / "players" / str(player_id),
                expect_item=True,
            ),
            ModelPlaceholder,
        )  # fmt: skip
