from __future__ import annotations

from abc import ABC
from typing import Generic, final, overload

from pydantic import Field, validate_call

from faceit.api.base import BaseResource, ModelPlaceholder
from faceit.api.pagination import (
    AsyncPageIterator,
    MaxItemsType,
    SyncPageIterator,
    pages,
)
from faceit.constants import GameID
from faceit.http import AsyncClient, SyncClient
from faceit.models import ItemPage
from faceit.models.custom_types import CountryCode
from faceit.types import (
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIItem,
    RawAPIPageResponse,
    RegionIdentifier,
)

from .players import PlayerID, PlayerIDValidated


class BaseRankings(
    BaseResource[ClientT],
    ABC,
    resource_path="rankings",
):
    __slots__ = ()


@final
class SyncRankings(BaseRankings[SyncClient], Generic[APIResponseFormatT]):
    __slots__ = ()

    @overload
    def unbounded(
        self: SyncRankings[Raw],
        game: GameID,
        region: RegionIdentifier,
        country: CountryCode | None = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @overload
    def unbounded(
        self: SyncRankings[Model],
        game: GameID,
        region: RegionIdentifier,
        country: CountryCode | None = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[ModelNotImplemented]: ...

    @validate_call
    def unbounded(
        self,
        game: GameID,
        region: RegionIdentifier,
        country: CountryCode | None = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse | ItemPage[ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / "games" / game / "regions" / region,
                params=self.__class__._build_params(
                    country=country, offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @overload
    def all_unbounded(
        self: SyncRankings[Raw],
        game: GameID,
        region: RegionIdentifier,
        country: CountryCode | None = None,
        max_items: MaxItemsType = pages(10),
    ) -> list[RawAPIItem]: ...

    @overload
    def all_unbounded(
        self: SyncRankings[Model],
        game: GameID,
        region: RegionIdentifier,
        country: CountryCode | None = None,
        max_items: MaxItemsType = pages(10),
    ) -> ItemPage[ModelNotImplemented]: ...

    @validate_call
    def all_unbounded(
        self,
        game: GameID,
        region: RegionIdentifier,
        country: CountryCode | None = None,
        max_items: MaxItemsType = pages(10),
    ) -> list[RawAPIItem] | ItemPage[ModelNotImplemented]:
        iterator = SyncPageIterator(
            self.unbounded, game, region, country, max_items=max_items
        )
        return iterator.collect()

    @overload
    def player(
        self: SyncRankings[Raw],
        game: GameID,
        region: RegionIdentifier,
        player_id: PlayerID,
        country: CountryCode | None = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @overload
    def player(
        self: SyncRankings[Model],
        game: GameID,
        region: RegionIdentifier,
        player_id: PlayerID,
        country: CountryCode | None = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> ModelNotImplemented: ...

    @validate_call
    def player(
        self,
        game: GameID,
        region: RegionIdentifier,
        player_id: PlayerIDValidated,
        country: CountryCode | None = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse | ModelNotImplemented:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / "games" / game / "regions" / region / "players" / str(player_id),
                params=self.__class__._build_params(
                    country=country, limit=limit
                ),
                expect_page=True
            ),
            ModelPlaceholder,
        )  # fmt: skip


@final
class AsyncRankings(BaseRankings[AsyncClient], Generic[APIResponseFormatT]):
    __slots__ = ()

    @overload
    async def unbounded(
        self: AsyncRankings[Raw],
        game: GameID,
        region: RegionIdentifier,
        country: CountryCode | None = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @overload
    async def unbounded(
        self: AsyncRankings[Model],
        game: GameID,
        region: RegionIdentifier,
        country: CountryCode | None = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[ModelNotImplemented]: ...

    @validate_call
    async def unbounded(
        self,
        game: GameID,
        region: RegionIdentifier,
        country: CountryCode | None = None,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse | ItemPage[ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / "games" / game / "regions" / region,
                params=self.__class__._build_params(
                    country=country, offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @overload
    async def all_unbounded(
        self: AsyncRankings[Raw],
        game: GameID,
        region: RegionIdentifier,
        country: CountryCode | None = None,
        max_items: MaxItemsType = pages(10),
    ) -> list[RawAPIItem]: ...

    @overload
    async def all_unbounded(
        self: AsyncRankings[Model],
        game: GameID,
        region: RegionIdentifier,
        country: CountryCode | None = None,
        max_items: MaxItemsType = pages(10),
    ) -> ItemPage[ModelNotImplemented]: ...

    @validate_call
    async def all_unbounded(
        self,
        game: GameID,
        region: RegionIdentifier,
        country: CountryCode | None = None,
        max_items: MaxItemsType = pages(10),
    ) -> list[RawAPIItem] | ItemPage[ModelNotImplemented]:
        iterator = AsyncPageIterator(
            self.unbounded, game, region, country, max_items=max_items
        )
        return await iterator.collect()

    @overload
    async def player(
        self: AsyncRankings[Raw],
        game: GameID,
        region: RegionIdentifier,
        player_id: PlayerID,
        country: CountryCode | None = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @overload
    async def player(
        self: AsyncRankings[Model],
        game: GameID,
        region: RegionIdentifier,
        player_id: PlayerID,
        country: CountryCode | None = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> ModelNotImplemented: ...

    @validate_call
    async def player(
        self,
        game: GameID,
        region: RegionIdentifier,
        player_id: PlayerIDValidated,
        country: CountryCode | None = None,
        *,
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse | ModelNotImplemented:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / "games" / game / "regions" / region / "players" / str(player_id),
                params=self.__class__._build_params(
                    country=country, limit=limit
                ),
                expect_page=True
            ),
            ModelPlaceholder,
        )  # fmt: skip
