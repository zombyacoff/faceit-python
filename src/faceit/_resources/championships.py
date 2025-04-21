from __future__ import annotations

import typing as t
from abc import ABC

from pydantic import AfterValidator, Field, validate_call

from faceit._typing import (
    Annotated,
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIItem,
    RawAPIPageResponse,
    TypeAlias,
    ValidUUID,
)
from faceit._utils import create_uuid_validator
from faceit.constants import EventCategory, ExpandedField, GameID
from faceit.http import AsyncClient, SyncClient
from faceit.models import Championship, ItemPage

from .base import BaseResource, FaceitResourcePath, ModelPlaceholder
from .pagination import MaxItemsType, MaxPages

_ChampionshipID: TypeAlias = ValidUUID
_ChampionshipIDValidator: TypeAlias = Annotated[
    _ChampionshipID,
    AfterValidator(create_uuid_validator(arg_name="championship identifier")),
]


class BaseChampionships(
    BaseResource[ClientT],
    ABC,
    resource_path=FaceitResourcePath.CHAMPIONSHIPS,
):
    __slots__ = ()


@t.final
class SyncChampionships(
    BaseChampionships[SyncClient], t.Generic[APIResponseFormatT]
):
    __slots__ = ()

    @t.overload
    def items(
        self: SyncChampionships[Raw],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def items(
        self: SyncChampionships[Model],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> ItemPage[Championship]: ...

    @validate_call
    def items(
        self,
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> t.Union[RawAPIPageResponse, ItemPage[Championship]]:
        return self._validate_response(
            self._client.get(
                self.PATH,
                params=self.__class__._build_params(
                    game=game, category=category, offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[Championship],
        )

    @t.overload
    def all_items(
        self: SyncChampionships[Raw],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        max_items: MaxItemsType = MaxPages(30),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def all_items(
        self: SyncChampionships[Model],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        max_items: MaxItemsType = MaxPages(30),
    ) -> ItemPage[Championship]: ...

    def all_items(
        self,
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        max_items: MaxItemsType = MaxPages(30),
    ) -> t.Union[RawAPIPageResponse, ItemPage[Championship]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.items, game, category, max_items=max_items
        )

    @t.overload
    def get(
        self: SyncChampionships[Raw],
        championship_id: _ChampionshipID,
        expanded: t.Optional[
            t.Union[ExpandedField, t.Sequence[ExpandedField]]
        ] = None,
    ) -> RawAPIItem: ...

    @t.overload
    def get(
        self: SyncChampionships[Model],
        championship_id: _ChampionshipID,
        expanded: t.Optional[
            t.Union[ExpandedField, t.Sequence[ExpandedField]]
        ] = None,
    ) -> ModelNotImplemented: ...

    @validate_call
    def get(
        self,
        championship_id: _ChampionshipIDValidator,
        expanded: t.Optional[
            t.Union[ExpandedField, t.Sequence[ExpandedField]]
        ] = None,
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(championship_id),
                params=self.__class__._build_params(expanded=expanded),
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    __call__ = get

    @t.overload
    def matches(
        self: SyncChampionships[Raw],
        championship_id: _ChampionshipID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def matches(
        self: SyncChampionships[Model],
        championship_id: _ChampionshipID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ModelNotImplemented: ...

    @validate_call
    def matches(
        self,
        championship_id: _ChampionshipIDValidator,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(championship_id) / "matches",
                params=self.__class__._build_params(
                    category=category, offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @t.overload
    def results(
        self: SyncChampionships[Raw],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def results(
        self: SyncChampionships[Model],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ModelNotImplemented: ...

    @validate_call
    def results(
        self,
        championship_id: _ChampionshipIDValidator,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(championship_id) / "results",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @t.overload
    def subscriptions(
        self: SyncChampionships[Raw],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def subscriptions(
        self: SyncChampionships[Model],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> ModelNotImplemented: ...

    @validate_call
    def subscriptions(
        self,
        championship_id: _ChampionshipIDValidator,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(championship_id) / "subscriptions",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )


@t.final
class AsyncChampionships(
    BaseChampionships[AsyncClient], t.Generic[APIResponseFormatT]
):
    __slots__ = ()

    @t.overload
    async def items(
        self: AsyncChampionships[Raw],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def items(
        self: AsyncChampionships[Model],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> ItemPage[Championship]: ...

    @validate_call
    async def items(
        self,
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> t.Union[RawAPIPageResponse, ItemPage[Championship]]:
        return self._validate_response(
            await self._client.get(
                self.PATH,
                params=self.__class__._build_params(
                    game=game, category=category, offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[Championship],
        )

    @t.overload
    def all_items(
        self: AsyncChampionships[Raw],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        max_items: MaxItemsType = MaxPages(30),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def all_items(
        self: AsyncChampionships[Model],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        max_items: MaxItemsType = MaxPages(30),
    ) -> ItemPage[Championship]: ...

    def all_items(
        self,
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        max_items: MaxItemsType = MaxPages(30),
    ) -> t.Union[RawAPIPageResponse, ItemPage[Championship]]:
        return self.__class__._async_page_iterator.gather_pages(
            self.items, game, category, max_items=max_items
        )

    @t.overload
    async def get(
        self: AsyncChampionships[Raw],
        championship_id: _ChampionshipID,
        expanded: t.Optional[
            t.Union[ExpandedField, t.Sequence[ExpandedField]]
        ] = None,
    ) -> RawAPIItem: ...

    @t.overload
    async def get(
        self: AsyncChampionships[Model],
        championship_id: _ChampionshipID,
        expanded: t.Optional[
            t.Union[ExpandedField, t.Sequence[ExpandedField]]
        ] = None,
    ) -> ModelNotImplemented: ...

    @validate_call
    async def get(
        self,
        championship_id: _ChampionshipIDValidator,
        expanded: t.Optional[
            t.Union[ExpandedField, t.Sequence[ExpandedField]]
        ] = None,
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(championship_id),
                params=self.__class__._build_params(expanded=expanded),
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    __call__ = get

    @t.overload
    async def matches(
        self: AsyncChampionships[Raw],
        championship_id: _ChampionshipID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def matches(
        self: AsyncChampionships[Model],
        championship_id: _ChampionshipID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ModelNotImplemented: ...

    @validate_call
    async def matches(
        self,
        championship_id: _ChampionshipIDValidator,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(championship_id) / "matches",
                params=self.__class__._build_params(
                    category=category, offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @t.overload
    async def results(
        self: AsyncChampionships[Raw],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def results(
        self: AsyncChampionships[Model],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ModelNotImplemented: ...

    @validate_call
    async def results(
        self,
        championship_id: _ChampionshipIDValidator,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(championship_id) / "results",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @t.overload
    async def subscriptions(
        self: AsyncChampionships[Raw],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def subscriptions(
        self: AsyncChampionships[Model],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> ModelNotImplemented: ...

    @validate_call
    async def subscriptions(
        self,
        championship_id: _ChampionshipIDValidator,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(championship_id) / "subscriptions",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )
