from __future__ import annotations

import typing as t
from abc import ABC

from pydantic import Field, validate_call

from faceit._typing import (
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIPageResponse,
)
from faceit.constants import GameID, Region  # noqa: TCH001
from faceit.http import AsyncClient, SyncClient
from faceit.models._custom_types import Country  # noqa: TCH001

from ._base import BaseResource, FaceitResourcePath, ModelPlaceholder
from ._players import PlayerID, PlayerIDValidator  # noqa: TCH001


class BaseRankings(
    BaseResource[ClientT],
    ABC,
    resource_path=FaceitResourcePath.RANKINGS,
):
    __slots__ = ()


class SyncRankings(BaseRankings[SyncClient], t.Generic[APIResponseFormatT]):
    __slots__ = ()

    @t.overload
    def world(
        self: SyncRankings[Raw],
        game: GameID,
        region: Region,
        country: t.Optional[Country] = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse]: ...

    @t.overload
    def world(
        self: SyncRankings[Model],
        game: GameID,
        region: Region,
        country: t.Optional[Country] = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ModelNotImplemented: ...

    @validate_call
    def world(
        self,
        game: GameID,
        region: Region,
        country: t.Optional[Country] = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.PATH / "games" / game / "regions" / region,
                params=self.__class__._build_params(
                    country=country, offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @t.overload
    def user(
        self: SyncRankings[Raw],
        game: GameID,
        region: Region,
        player_id: PlayerID,
        country: t.Optional[Country] = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse]: ...

    @t.overload
    def user(
        self: SyncRankings[Model],
        game: GameID,
        region: Region,
        player_id: PlayerID,
        country: t.Optional[Country] = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[ModelNotImplemented]: ...

    @validate_call
    def user(
        self,
        game: GameID,
        region: Region,
        player_id: PlayerIDValidator,
        country: t.Optional[Country] = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        # fmt: off
        return self._validate_response(
            self._client.get(
                self.PATH / "games" / game / "regions" / region / "players" / str(player_id),
                params=self.__class__._build_params(
                    country=country, limit=limit
                ),
                expect_page=True
            ),
            ModelPlaceholder,
        )
        # fmt: on


class AsyncRankings(BaseRankings[AsyncClient], t.Generic[APIResponseFormatT]):
    __slots__ = ()
