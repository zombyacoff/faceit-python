from __future__ import annotations

from abc import ABC
from typing import Annotated, Generic, TypeAlias, final, overload

from pydantic import AfterValidator, Field, validate_call

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
from faceit.types import (
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIItem,
    RawAPIPageResponse,
)

_TeamID: TypeAlias = str
_TeamIDValidated: TypeAlias = Annotated[
    _TeamID, AfterValidator(str)  # TODO: Validation function (maybe `FaceitID`?)
]


class BaseTeams(
    BaseResource[ClientT],
    ABC,
    resource_path="teams",
):
    __slots__ = ()


@final
class SyncTeams(BaseTeams[SyncClient], Generic[APIResponseFormatT]):
    __slots__ = ()

    @overload
    def get(self: SyncTeams[Raw], team_id: _TeamID) -> RawAPIItem: ...

    @overload
    def get(self: SyncTeams[Model], team_id: _TeamID) -> ModelNotImplemented: ...

    @validate_call
    def get(self, team_id: _TeamIDValidated) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            self._client.get(self.__class__.PATH / team_id, expect_item=True),
            ModelPlaceholder,
        )

    __call__ = get

    @overload
    def stats(self: SyncTeams[Raw], team_id: _TeamID, game: GameID) -> RawAPIItem: ...

    @overload
    def stats(
        self: SyncTeams[Model], team_id: _TeamID, game: GameID
    ) -> ModelNotImplemented: ...

    @validate_call
    def stats(
        self, team_id: _TeamIDValidated, game: GameID
    ) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / team_id / "stats" / game,
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    @overload
    def tournaments(
        self: SyncTeams[Raw],
        team_id: _TeamID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @overload
    def tournaments(
        self: SyncTeams[Model],
        team_id: _TeamID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[ModelNotImplemented]: ...

    @validate_call
    def tournaments(
        self,
        team_id: _TeamIDValidated,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse | ItemPage[ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / team_id / "tournaments",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @overload
    def all_tournaments(
        self: SyncTeams[Raw], team_id: _TeamID, max_items: MaxItemsType = pages(30)
    ) -> list[RawAPIItem]: ...

    @overload
    def all_tournaments(
        self: SyncTeams[Model], team_id: _TeamID, max_items: MaxItemsType = pages(30)
    ) -> ItemPage[ModelNotImplemented]: ...

    def all_tournaments(
        self, team_id: _TeamIDValidated, max_items: MaxItemsType = pages(30)
    ) -> list[RawAPIItem] | ItemPage[ModelNotImplemented]:
        iterator = SyncPageIterator(self.tournaments, team_id, max_items=max_items)
        return iterator.collect()


@final
class AsyncTeams(BaseTeams[AsyncClient], Generic[APIResponseFormatT]):
    __slots__ = ()

    @overload
    async def get(self: AsyncTeams[Raw], team_id: _TeamID) -> RawAPIItem: ...

    @overload
    async def get(self: AsyncTeams[Model], team_id: _TeamID) -> ModelNotImplemented: ...

    @validate_call
    async def get(self, team_id: _TeamIDValidated) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            await self._client.get(self.__class__.PATH / team_id, expect_item=True),
            ModelPlaceholder,
        )

    __call__ = get

    @overload
    async def stats(
        self: AsyncTeams[Raw], team_id: _TeamID, game: GameID
    ) -> RawAPIItem: ...

    @overload
    async def stats(
        self: AsyncTeams[Model], team_id: _TeamID, game: GameID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def stats(
        self, team_id: _TeamIDValidated, game: GameID
    ) -> RawAPIItem | ModelNotImplemented:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / team_id / "stats" / game,
                expect_item=True,
            ),
            ModelPlaceholder,
        )

    @overload
    async def tournaments(
        self: AsyncTeams[Raw],
        team_id: _TeamID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @overload
    async def tournaments(
        self: AsyncTeams[Model],
        team_id: _TeamID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[ModelNotImplemented]: ...

    @validate_call
    async def tournaments(
        self,
        team_id: _TeamIDValidated,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse | ItemPage[ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / team_id / "tournaments",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @overload
    async def all_tournaments(
        self: AsyncTeams[Raw], team_id: _TeamID, max_items: MaxItemsType = pages(30)
    ) -> list[RawAPIItem]: ...

    @overload
    async def all_tournaments(
        self: AsyncTeams[Model], team_id: _TeamID, max_items: MaxItemsType = pages(30)
    ) -> ItemPage[ModelNotImplemented]: ...

    async def all_tournaments(
        self, team_id: _TeamIDValidated, max_items: MaxItemsType = pages(30)
    ) -> list[RawAPIItem] | ItemPage[ModelNotImplemented]:
        iterator = AsyncPageIterator(self.tournaments, team_id, max_items=max_items)
        return await iterator.collect()
