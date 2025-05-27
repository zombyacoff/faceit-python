from __future__ import annotations

import typing
from abc import ABC

from pydantic import AfterValidator, Field, validate_call
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
from faceit.utils import create_uuid_validator

from .players import PlayerID, PlayerIDValidated  # noqa: TC001

_LeagueID: TypeAlias = ValidUUID
_LeagueIDValidated: TypeAlias = Annotated[
    _LeagueID,
    AfterValidator(create_uuid_validator(arg_name="league ID")),
]
_SeasonID: TypeAlias = Annotated[int, Field(ge=1)]


class BaseLeagues(
    BaseResource[ClientT],
    ABC,
    resource_path=FaceitResourcePath.LEAGUES,
):
    __slots__ = ()


class SyncLeagues(BaseLeagues[SyncClient], typing.Generic[APIResponseFormatT]):
    __slots__ = ()

    @typing.overload
    def get(self: SyncLeagues[Raw], matchmaking_id: _LeagueID) -> RawAPIItem: ...

    @typing.overload
    def get(
        self: SyncLeagues[Model], matchmaking_id: _LeagueID
    ) -> ModelNotImplemented: ...

    @validate_call
    def get(
        self, matchmaking_id: _LeagueIDValidated
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(matchmaking_id), expect_item=True
            ),
            ModelPlaceholder,
        )

    __call__ = get

    @typing.overload
    def season(
        self: SyncLeagues[Raw], matchmaking_id: _LeagueID, season_id: _SeasonID
    ) -> RawAPIItem: ...

    @typing.overload
    def season(
        self: SyncLeagues[Model], matchmaking_id: _LeagueID, season_id: _SeasonID
    ) -> ModelNotImplemented: ...

    @validate_call
    def season(
        self, matchmaking_id: _LeagueIDValidated, season_id: _SeasonID
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(matchmaking_id) / "seasons" / str(season_id),
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    @typing.overload
    def player(
        self: SyncLeagues[Raw],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
        player_id: PlayerID,
    ) -> RawAPIItem: ...

    @typing.overload
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
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        # fmt: off
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(matchmaking_id) / "seasons" / str(season_id) / "players" / str(player_id),
                expect_item=True,
            ),
            ModelPlaceholder,
        )
        # fmt: on


class AsyncLeagues(BaseLeagues[AsyncClient], typing.Generic[APIResponseFormatT]):
    __slots__ = ()

    @typing.overload
    async def get(self: AsyncLeagues[Raw], matchmaking_id: _LeagueID) -> RawAPIItem: ...

    @typing.overload
    async def get(
        self: AsyncLeagues[Model], matchmaking_id: _LeagueID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def get(
        self, matchmaking_id: _LeagueIDValidated
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(matchmaking_id), expect_item=True
            ),
            ModelPlaceholder,
        )

    __call__ = get

    @typing.overload
    async def season(
        self: AsyncLeagues[Raw], matchmaking_id: _LeagueID, season_id: _SeasonID
    ) -> RawAPIItem: ...

    @typing.overload
    async def season(
        self: AsyncLeagues[Model], matchmaking_id: _LeagueID, season_id: _SeasonID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def season(
        self, matchmaking_id: _LeagueIDValidated, season_id: _SeasonID
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(matchmaking_id) / "seasons" / str(season_id),
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    @typing.overload
    async def player(
        self: AsyncLeagues[Raw],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
        player_id: PlayerID,
    ) -> RawAPIItem: ...

    @typing.overload
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
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        # fmt: off
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(matchmaking_id) / "seasons" / str(season_id) / "players" / str(player_id),
                expect_item=True,
            ),
            ModelPlaceholder,
        )
        # fmt: on
