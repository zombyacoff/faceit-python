from __future__ import annotations

import typing as t
from abc import ABC

import typing_extensions as te
from pydantic import AfterValidator, Field, validate_call

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
from faceit.utils import create_uuid_validator

from .players import PlayerID, PlayerIDValidator  # noqa: TCH001

_LeagueID: te.TypeAlias = ValidUUID
_LeagueIDValidator: te.TypeAlias = te.Annotated[
    _LeagueID,
    AfterValidator(create_uuid_validator(arg_name="league identifier")),
]
_SeasonID: te.TypeAlias = te.Annotated[int, Field(ge=1)]


class BaseLeagues(
    BaseResource[ClientT],
    ABC,
    resource_path=FaceitResourcePath.LEAGUES,
):
    __slots__ = ()


class SyncLeagues(BaseLeagues[SyncClient], t.Generic[APIResponseFormatT]):
    __slots__ = ()

    @t.overload
    def get(
        self: SyncLeagues[Raw], matchmaking_id: _LeagueID
    ) -> RawAPIItem: ...

    @t.overload
    def get(
        self: SyncLeagues[Model], matchmaking_id: _LeagueID
    ) -> ModelNotImplemented: ...

    @validate_call
    def get(
        self, matchmaking_id: _LeagueIDValidator
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(matchmaking_id), expect_item=True
            ),
            ModelPlaceholder,
        )

    __call__ = get

    @t.overload
    def season(
        self: SyncLeagues[Raw],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
    ) -> RawAPIItem: ...

    @t.overload
    def season(
        self: SyncLeagues[Model],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
    ) -> ModelNotImplemented: ...

    @validate_call
    def season(
        self, matchmaking_id: _LeagueIDValidator, season_id: _SeasonID
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(matchmaking_id) / "seasons" / str(season_id),
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    @t.overload
    def player(
        self: SyncLeagues[Raw],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
        player_id: PlayerID,
    ) -> RawAPIItem: ...

    @t.overload
    def player(
        self: SyncLeagues[Model],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
        player_id: PlayerID,
    ) -> ModelNotImplemented: ...

    @validate_call
    def player(
        self,
        matchmaking_id: _LeagueIDValidator,
        season_id: _SeasonID,
        player_id: PlayerIDValidator,
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        # fmt: off
        return self._validate_response(
            self._client.get(
                self.PATH / str(matchmaking_id) / "seasons" / str(season_id) / "players" / str(player_id),
                expect_item=True,
            ),
            ModelPlaceholder,
        )
        # fmt: on


class AsyncLeagues(BaseLeagues[AsyncClient], t.Generic[APIResponseFormatT]):
    __slots__ = ()

    @t.overload
    async def get(
        self: AsyncLeagues[Raw], matchmaking_id: _LeagueID
    ) -> RawAPIItem: ...

    @t.overload
    async def get(
        self: AsyncLeagues[Model], matchmaking_id: _LeagueID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def get(
        self, matchmaking_id: _LeagueIDValidator
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(matchmaking_id), expect_item=True
            ),
            ModelPlaceholder,
        )

    __call__ = get

    @t.overload
    async def season(
        self: AsyncLeagues[Raw],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
    ) -> RawAPIItem: ...

    @t.overload
    async def season(
        self: AsyncLeagues[Model],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
    ) -> ModelNotImplemented: ...

    @validate_call
    async def season(
        self, matchmaking_id: _LeagueIDValidator, season_id: _SeasonID
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(matchmaking_id) / "seasons" / str(season_id),
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    @t.overload
    async def player(
        self: AsyncLeagues[Raw],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
        player_id: PlayerID,
    ) -> RawAPIItem: ...

    @t.overload
    async def player(
        self: AsyncLeagues[Model],
        matchmaking_id: _LeagueID,
        season_id: _SeasonID,
        player_id: PlayerID,
    ) -> ModelNotImplemented: ...

    @validate_call
    async def player(
        self,
        matchmaking_id: _LeagueIDValidator,
        season_id: _SeasonID,
        player_id: PlayerIDValidator,
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        # fmt: off
        return self._validate_response(
            await self._client.get(
                self.PATH / str(matchmaking_id) / "seasons" / str(season_id) / "players" / str(player_id),
                expect_item=True,
            ),
            ModelPlaceholder,
        )
        # fmt: on
