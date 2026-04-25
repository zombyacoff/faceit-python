# mypy: disable-error-code="no-any-return"
from __future__ import annotations

import typing
from abc import ABC

from pydantic import Field, validate_call

from faceit.http import AsyncClient, SyncClient
from faceit.models import ItemPage  # noqa: TC001
from faceit.resources.base import BaseResource, FaceitResourcePath, ModelPlaceholder
from faceit.resources.pagination import MaxItems, MaxItemsType
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
    resource_path=FaceitResourcePath.GAMES,
):
    __slots__ = ()


@typing.final
class SyncGames(BaseGames[SyncClient], typing.Generic[APIResponseFormatT]):
    __slots__ = ()

    @typing.overload
    def items(
        self: SyncGames[Raw],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @typing.overload
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
    ) -> typing.Union[RawAPIPageResponse, ItemPage[ModelNotImplemented]]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH,
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @typing.overload
    def all_items(
        self: SyncGames[Raw], max_items: MaxItemsType = MaxItems.SAFE
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    def all_items(
        self: SyncGames[Model], max_items: MaxItemsType = MaxItems.SAFE
    ) -> ItemPage[ModelNotImplemented]: ...

    def all_items(
        self, max_items: MaxItemsType = MaxItems.SAFE
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[ModelNotImplemented]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.items, max_items=max_items
        )


@typing.final
class AsyncGames(BaseGames[AsyncClient], typing.Generic[APIResponseFormatT]):
    __slots__ = ()

    @typing.overload
    async def items(
        self: AsyncGames[Raw],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @typing.overload
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
    ) -> typing.Union[RawAPIPageResponse, ItemPage[ModelNotImplemented]]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH,
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @typing.overload
    async def all_items(
        self: AsyncGames[Raw], max_items: MaxItemsType = MaxItems.SAFE
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    async def all_items(
        self: AsyncGames[Model], max_items: MaxItemsType = MaxItems.SAFE
    ) -> ItemPage[ModelNotImplemented]: ...

    async def all_items(
        self, max_items: MaxItemsType = MaxItems.SAFE
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[ModelNotImplemented]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.items, max_items=max_items
        )
