from __future__ import annotations

from abc import ABC
from collections.abc import Sequence  # noqa: TC003
from typing import Annotated, Generic, TypeAlias, final, overload

from pydantic import AfterValidator, Field, validate_call

from faceit.api.base import BaseResource, ModelPlaceholder
from faceit.api.pagination import (
    AsyncPageIterator,
    MaxItemsType,
    SyncPageIterator,
    pages,
)
from faceit.constants import EventCategory, ExpandedField, GameID
from faceit.http import AsyncClient, SyncClient
from faceit.models import Championship, ItemPage
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
    AfterValidator(create_uuid_validator(arg_name="championship_id")),
]


class BaseChampionships(
    BaseResource[ClientT],
    ABC,
    resource_path="championships",
):
    __slots__ = ()


@final
class SyncChampionships(BaseChampionships[SyncClient], Generic[APIResponseFormatT]):
    __slots__ = ()

    @overload
    def items(
        self: SyncChampionships[Raw],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @overload
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
    ) -> RawAPIPageResponse | ItemPage[Championship]:
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

    @overload
    def all_items(
        self: SyncChampionships[Raw],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        max_items: MaxItemsType = pages(30),
    ) -> list[RawAPIItem]: ...

    @overload
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
    ) -> list[RawAPIItem] | ItemPage[Championship]:
        iterator = SyncPageIterator(self.items, game, category, max_items=max_items)
        return iterator.collect()

    @overload
    def get(
        self: SyncChampionships[Raw],
        championship_id: _ChampionshipID,
        expanded: ExpandedField | Sequence[ExpandedField] | None = None,
    ) -> RawAPIItem: ...

    @overload
    def get(
        self: SyncChampionships[Model],
        championship_id: _ChampionshipID,
        expanded: ExpandedField | Sequence[ExpandedField] | None = None,
    ) -> ModelNotImplemented: ...

    @validate_call
    def get(
        self,
        championship_id: _ChampionshipIDValidated,
        expanded: ExpandedField | Sequence[ExpandedField] | None = None,
    ) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(championship_id),
                params=self.__class__._build_params(expanded=expanded),
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    __call__ = get

    @overload
    def matches(
        self: SyncChampionships[Raw],
        championship_id: _ChampionshipID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @overload
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
    ) -> RawAPIPageResponse | ModelNotImplemented:
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

    @overload
    def results(
        self: SyncChampionships[Raw],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @overload
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
    ) -> RawAPIPageResponse | ModelNotImplemented:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(championship_id) / "results",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @overload
    def subscriptions(
        self: SyncChampionships[Raw],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @overload
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
    ) -> RawAPIPageResponse | ModelNotImplemented:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(championship_id) / "subscriptions",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )


@final
class AsyncChampionships(BaseChampionships[AsyncClient], Generic[APIResponseFormatT]):
    __slots__ = ()

    @overload
    async def items(
        self: AsyncChampionships[Raw],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @overload
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
    ) -> RawAPIPageResponse | ItemPage[Championship]:
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

    @overload
    async def all_items(
        self: AsyncChampionships[Raw],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        max_items: MaxItemsType = pages(30),
    ) -> list[RawAPIItem]: ...

    @overload
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
    ) -> list[RawAPIItem] | ItemPage[Championship]:
        iterator = AsyncPageIterator(self.items, game, category, max_items=max_items)
        return await iterator.collect()

    @overload
    async def get(
        self: AsyncChampionships[Raw],
        championship_id: _ChampionshipID,
        expanded: ExpandedField | Sequence[ExpandedField] | None = None,
    ) -> RawAPIItem: ...

    @overload
    async def get(
        self: AsyncChampionships[Model],
        championship_id: _ChampionshipID,
        expanded: ExpandedField | Sequence[ExpandedField] | None = None,
    ) -> ModelNotImplemented: ...

    @validate_call
    async def get(
        self,
        championship_id: _ChampionshipIDValidated,
        expanded: ExpandedField | Sequence[ExpandedField] | None = None,
    ) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(championship_id),
                params=self.__class__._build_params(expanded=expanded),
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    __call__ = get

    @overload
    async def matches(
        self: AsyncChampionships[Raw],
        championship_id: _ChampionshipID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @overload
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
    ) -> RawAPIPageResponse | ModelNotImplemented:
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

    @overload
    async def results(
        self: AsyncChampionships[Raw],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @overload
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
    ) -> RawAPIPageResponse | ModelNotImplemented:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(championship_id) / "results",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @overload
    async def subscriptions(
        self: AsyncChampionships[Raw],
        championship_id: _ChampionshipID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @overload
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
    ) -> RawAPIPageResponse | ModelNotImplemented:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(championship_id) / "subscriptions",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )
