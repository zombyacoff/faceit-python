from __future__ import annotations

from abc import ABC
from typing import Generic, final, overload

from pydantic import Field, validate_call

from faceit.api.base import BaseResource, ModelPlaceholder
from faceit.api.pagination import (
    AsyncPageIterator,
    MaxItemsType,
    SyncPageIterator,
)
from faceit.http import AsyncClient, SyncClient
from faceit.models import ItemPage  # noqa: TC001
from faceit.types import (
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIItem,
    RawAPIPageResponse,
)


class BaseGames(
    BaseResource[ClientT],
    ABC,
    resource_path="games",
):
    __slots__ = ()


@final
class SyncGames(BaseGames[SyncClient], Generic[APIResponseFormatT]):
    __slots__ = ()

    @overload
    def items(
        self: SyncGames[Raw],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @overload
    def items(
        self: SyncGames[Model],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[ModelNotImplemented]: ...

    @validate_call
    def items(
        self,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse | ItemPage[ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH,
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @overload
    def all_items(
        self: SyncGames[Raw], max_items: MaxItemsType = "safe"
    ) -> list[RawAPIItem]: ...

    @overload
    def all_items(
        self: SyncGames[Model], max_items: MaxItemsType = "safe"
    ) -> ItemPage[ModelNotImplemented]: ...

    def all_items(
        self, max_items: MaxItemsType = "safe"
    ) -> list[RawAPIItem] | ItemPage[ModelNotImplemented]:
        iterator = SyncPageIterator(self.items, max_items=max_items)
        return iterator.collect()


@final
class AsyncGames(BaseGames[AsyncClient], Generic[APIResponseFormatT]):
    __slots__ = ()

    @overload
    async def items(
        self: AsyncGames[Raw],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @overload
    async def items(
        self: AsyncGames[Model],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[ModelNotImplemented]: ...

    @validate_call
    async def items(
        self,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse | ItemPage[ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH,
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @overload
    async def all_items(
        self: AsyncGames[Raw], max_items: MaxItemsType = "safe"
    ) -> list[RawAPIItem]: ...

    @overload
    async def all_items(
        self: AsyncGames[Model], max_items: MaxItemsType = "safe"
    ) -> ItemPage[ModelNotImplemented]: ...

    async def all_items(
        self, max_items: MaxItemsType = "safe"
    ) -> list[RawAPIItem] | ItemPage[ModelNotImplemented]:
        iterator = AsyncPageIterator(self.items, max_items=max_items)
        return await iterator.collect()
