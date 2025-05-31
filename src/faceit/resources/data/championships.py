# mypy: disable-error-code="no-any-return"
from __future__ import annotations

import typing
from abc import ABC

from pydantic import AfterValidator, Field, validate_call
from typing_extensions import Annotated, TypeAlias

from faceit.constants import EventCategory, ExpandedField, GameID
from faceit.http import AsyncClient, SyncClient
from faceit.models import Championship, ItemPage
from faceit.resources.base import BaseResource, FaceitResourcePath, ModelPlaceholder
from faceit.resources.pagination import MaxItemsType, pages
from faceit.types import (
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIItem,
    RawAPIPageResponse,
    ValidUUID,
)
from faceit.utils import create_uuid_validator

_ChampionshipID: TypeAlias = ValidUUID
_ChampionshipIDValidated: TypeAlias = Annotated[
    _ChampionshipID,
    AfterValidator(create_uuid_validator(arg_name="championship ID")),
]


class BaseChampionships(
    BaseResource[ClientT],
    ABC,
    resource_path=FaceitResourcePath.CHAMPIONSHIPS,
):
    __slots__ = ()


@typing.final
class SyncChampionships(
    BaseChampionships[SyncClient], typing.Generic[APIResponseFormatT]
):
    __slots__ = ()

    @typing.overload
    def items(
        self: SyncChampionships[Raw],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @typing.overload
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
    ) -> typing.Union[RawAPIPageResponse, ItemPage[Championship]]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH,
                params=self.__class__._build_params(
                    game=game, category=category, offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[Championship],
        )

    @typing.overload
    def all_items(
        self: SyncChampionships[Raw],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        max_items: MaxItemsType = pages(30),
    ) -> RawAPIPageResponse: ...

    @typing.overload
    def all_items(
        self: SyncChampionships[Model],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        max_items: MaxItemsType = pages(30),
    ) -> ItemPage[Championship]: ...

    def all_items(
        self,
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        max_items: MaxItemsType = pages(30),
    ) -> typing.Union[RawAPIPageResponse, ItemPage[Championship]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.items, game, category, max_items=max_items
        )

    @typing.overload
    def get(
        self: SyncChampionships[Raw],
        championship_id: _ChampionshipID,
        expanded: typing.Optional[
            typing.Union[ExpandedField, typing.Sequence[ExpandedField]]
        ] = None,
    ) -> RawAPIItem: ...

    @typing.overload
    def get(
        self: SyncChampionships[Model],
        championship_id: _ChampionshipID,
        expanded: typing.Optional[
            typing.Union[ExpandedField, typing.Sequence[ExpandedField]]
        ] = None,
    ) -> ModelNotImplemented: ...

    @validate_call
    def get(
        self,
        championship_id: _ChampionshipIDValidated,
        expanded: typing.Optional[
            typing.Union[ExpandedField, typing.Sequence[ExpandedField]]
        ] = None,
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(championship_id),
                params=self.__class__._build_params(expanded=expanded),
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    __call__ = get

    @typing.overload
    def matches(
        self: SyncChampionships[Raw],
        championship_id: _ChampionshipID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @typing.overload
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
        championship_id: _ChampionshipIDValidated,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> typing.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(championship_id) / "matches",
                params=self.__class__._build_params(
                    category=category, offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @typing.overload
    def results(
        self: SyncChampionships[Raw],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @typing.overload
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
        championship_id: _ChampionshipIDValidated,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> typing.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(championship_id) / "results",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @typing.overload
    def subscriptions(
        self: SyncChampionships[Raw],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @typing.overload
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
        championship_id: _ChampionshipIDValidated,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> typing.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(championship_id) / "subscriptions",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )


@typing.final
class AsyncChampionships(
    BaseChampionships[AsyncClient], typing.Generic[APIResponseFormatT]
):
    __slots__ = ()

    @typing.overload
    async def items(
        self: AsyncChampionships[Raw],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @typing.overload
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
    ) -> typing.Union[RawAPIPageResponse, ItemPage[Championship]]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH,
                params=self.__class__._build_params(
                    game=game, category=category, offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[Championship],
        )

    @typing.overload
    async def all_items(
        self: AsyncChampionships[Raw],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        max_items: MaxItemsType = pages(30),
    ) -> RawAPIPageResponse: ...

    @typing.overload
    async def all_items(
        self: AsyncChampionships[Model],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        max_items: MaxItemsType = pages(30),
    ) -> ItemPage[Championship]: ...

    async def all_items(
        self,
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        max_items: MaxItemsType = pages(30),
    ) -> typing.Union[RawAPIPageResponse, ItemPage[Championship]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.items, game, category, max_items=max_items
        )

    @typing.overload
    async def get(
        self: AsyncChampionships[Raw],
        championship_id: _ChampionshipID,
        expanded: typing.Optional[
            typing.Union[ExpandedField, typing.Sequence[ExpandedField]]
        ] = None,
    ) -> RawAPIItem: ...

    @typing.overload
    async def get(
        self: AsyncChampionships[Model],
        championship_id: _ChampionshipID,
        expanded: typing.Optional[
            typing.Union[ExpandedField, typing.Sequence[ExpandedField]]
        ] = None,
    ) -> ModelNotImplemented: ...

    @validate_call
    async def get(
        self,
        championship_id: _ChampionshipIDValidated,
        expanded: typing.Optional[
            typing.Union[ExpandedField, typing.Sequence[ExpandedField]]
        ] = None,
    ) -> typing.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(championship_id),
                params=self.__class__._build_params(expanded=expanded),
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    __call__ = get

    @typing.overload
    async def matches(
        self: AsyncChampionships[Raw],
        championship_id: _ChampionshipID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @typing.overload
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
        championship_id: _ChampionshipIDValidated,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> typing.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(championship_id) / "matches",
                params=self.__class__._build_params(
                    category=category, offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @typing.overload
    async def results(
        self: AsyncChampionships[Raw],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @typing.overload
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
        championship_id: _ChampionshipIDValidated,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> typing.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(championship_id) / "results",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @typing.overload
    async def subscriptions(
        self: AsyncChampionships[Raw],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @typing.overload
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
        championship_id: _ChampionshipIDValidated,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> typing.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(championship_id) / "subscriptions",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )
