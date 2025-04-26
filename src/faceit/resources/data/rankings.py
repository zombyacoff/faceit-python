from __future__ import annotations

import typing as t
from abc import ABC

from pydantic import Field, validate_call

from faceit.constants import GameID, Region  # noqa: TCH001
from faceit.http import AsyncClient, SyncClient
from faceit.models.custom_types import CountryCode  # noqa: TCH001
from faceit.resources.base import (
    BaseResource,
    FaceitResourcePath,
    ModelPlaceholder,
)
from faceit.resources.pagination import MaxItemsType, MaxPages
from faceit.types import (
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIItem,
    RawAPIPageResponse,
)

from .players import PlayerID, PlayerIDValidator  # noqa: TCH001


class BaseRankings(
    BaseResource[ClientT],
    ABC,
    resource_path=FaceitResourcePath.RANKINGS,
):
    __slots__ = ()


class SyncRankings(BaseRankings[SyncClient], t.Generic[APIResponseFormatT]):
    __slots__ = ()

    @t.overload
    def unbounded(
        self: SyncRankings[Raw],
        game: GameID,
        region: Region,
        country: t.Optional[CountryCode] = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse]: ...

    @t.overload
    def unbounded(
        self: SyncRankings[Model],
        game: GameID,
        region: Region,
        country: t.Optional[CountryCode] = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ModelNotImplemented: ...

    @validate_call
    def unbounded(
        self,
        game: GameID,
        region: Region,
        country: t.Optional[CountryCode] = None,
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
    def all_unbounded(
        self: SyncRankings[Raw],
        game: GameID,
        region: Region,
        country: t.Optional[CountryCode] = None,
        *,
        max_items: MaxItemsType = MaxPages(10),
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    def all_unbounded(
        self: SyncRankings[Model],
        game: GameID,
        region: Region,
        country: t.Optional[CountryCode] = None,
        *,
        max_items: MaxItemsType = MaxPages(10),
    ) -> ModelNotImplemented: ...

    def all_unbounded(
        self,
        game: GameID,
        region: Region,
        country: t.Optional[CountryCode] = None,
        *,
        max_items: MaxItemsType = MaxPages(10),
    ) -> t.Union[t.List[RawAPIItem], ModelNotImplemented]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.unbounded, game, region, country, max_items=max_items
        )

    @t.overload
    def player(
        self: SyncRankings[Raw],
        game: GameID,
        region: Region,
        player_id: PlayerID,
        country: t.Optional[CountryCode] = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse]: ...

    @t.overload
    def player(
        self: SyncRankings[Model],
        game: GameID,
        region: Region,
        player_id: PlayerID,
        country: t.Optional[CountryCode] = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[ModelNotImplemented]: ...

    @validate_call
    def player(
        self,
        game: GameID,
        region: Region,
        player_id: PlayerIDValidator,
        country: t.Optional[CountryCode] = None,
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

    @t.overload
    async def unbounded(
        self: AsyncRankings[Raw],
        game: GameID,
        region: Region,
        country: t.Optional[CountryCode] = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse]: ...

    @t.overload
    async def unbounded(
        self: AsyncRankings[Model],
        game: GameID,
        region: Region,
        country: t.Optional[CountryCode] = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ModelNotImplemented: ...

    @validate_call
    async def unbounded(
        self,
        game: GameID,
        region: Region,
        country: t.Optional[CountryCode] = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.PATH / "games" / game / "regions" / region,
                params=self.__class__._build_params(
                    country=country, offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @t.overload
    async def all_unbounded(
        self: AsyncRankings[Raw],
        game: GameID,
        region: Region,
        country: t.Optional[CountryCode] = None,
        *,
        max_items: MaxItemsType = MaxPages(10),
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    async def all_unbounded(
        self: AsyncRankings[Model],
        game: GameID,
        region: Region,
        country: t.Optional[CountryCode] = None,
        *,
        max_items: MaxItemsType = MaxPages(10),
    ) -> ModelNotImplemented: ...

    async def all_unbounded(
        self,
        game: GameID,
        region: Region,
        country: t.Optional[CountryCode] = None,
        *,
        max_items: MaxItemsType = MaxPages(10),
    ) -> t.Union[t.List[RawAPIItem], ModelNotImplemented]:
        return self.__class__._async_page_iterator.gather_pages(
            self.unbounded, game, region, country, max_items=max_items
        )

    @t.overload
    async def player(
        self: AsyncRankings[Raw],
        game: GameID,
        region: Region,
        player_id: PlayerID,
        country: t.Optional[CountryCode] = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse]: ...

    @t.overload
    async def player(
        self: AsyncRankings[Model],
        game: GameID,
        region: Region,
        player_id: PlayerID,
        country: t.Optional[CountryCode] = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[ModelNotImplemented]: ...

    @validate_call
    async def player(
        self,
        game: GameID,
        region: Region,
        player_id: PlayerIDValidator,
        country: t.Optional[CountryCode] = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        # fmt: off
        return self._validate_response(
            await self._client.get(
                self.PATH / "games" / game / "regions" / region / "players" / str(player_id),
                params=self.__class__._build_params(
                    country=country, limit=limit
                ),
                expect_page=True
            ),
            ModelPlaceholder,
        )
        # fmt: on
