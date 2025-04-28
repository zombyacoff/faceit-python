from __future__ import annotations

import typing as t
from abc import ABC

import typing_extensions as te
from pydantic import AfterValidator, Field, validate_call

from faceit.constants import GameID  # noqa: TCH001
from faceit.http import AsyncClient, SyncClient
from faceit.resources.base import (
    BaseResource,
    FaceitResourcePath,
    ModelPlaceholder,
)
from faceit.resources.pagination import MaxItemsType, pages
from faceit.types import (
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIItem,
    RawAPIPageResponse,
)

_TeamID: te.TypeAlias = str
_TeamIDValidator: te.TypeAlias = te.Annotated[
    _TeamID, AfterValidator(str)  # TODO: Validation function
]


class BaseTeams(
    BaseResource[ClientT],
    ABC,
    resource_path=FaceitResourcePath.TEAMS,
):
    __slots__ = ()


class SyncTeams(BaseTeams[SyncClient], t.Generic[APIResponseFormatT]):
    __slots__ = ()

    @t.overload
    def get(self: SyncTeams[Raw], team_id: _TeamID) -> RawAPIItem: ...

    @t.overload
    def get(
        self: SyncTeams[Model], team_id: _TeamID
    ) -> ModelNotImplemented: ...

    @validate_call
    def get(
        self, team_id: _TeamIDValidator
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(self.PATH / team_id, expect_item=True),
            ModelPlaceholder,
        )

    __call__ = get

    @te.deprecated(
        "`details` is deprecated and will be removed in a future release. "
        "Use `get` instead."
    )
    def details(self, team_id: _TeamID) -> t.Any:
        return self.get(team_id)

    @t.overload
    def stats(
        self: SyncTeams[Raw], team_id: _TeamID, game: GameID
    ) -> RawAPIItem: ...

    @t.overload
    def stats(
        self: SyncTeams[Model], team_id: _TeamID, game: GameID
    ) -> ModelNotImplemented: ...

    @validate_call
    def stats(
        self, team_id: _TeamIDValidator, game: GameID
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.PATH / team_id / "stats" / game, expect_item=True
            ),
            ModelPlaceholder,
        )

    @t.overload
    def tournaments(
        self: SyncTeams[Raw],
        team_id: _TeamID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def tournaments(
        self: SyncTeams[Model],
        team_id: _TeamID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ModelNotImplemented: ...

    @validate_call
    def tournaments(
        self,
        team_id: _TeamIDValidator,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.PATH / team_id / "tournaments",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @t.overload
    def all_tournaments(
        self: SyncTeams[Raw],
        team_id: _TeamID,
        *,
        max_items: MaxItemsType = pages(30),
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    def all_tournaments(
        self: SyncTeams[Model],
        team_id: _TeamID,
        *,
        max_items: MaxItemsType = pages(30),
    ) -> ModelNotImplemented: ...

    def all_tournaments(
        self,
        team_id: _TeamIDValidator,
        *,
        max_items: MaxItemsType = pages(30),
    ) -> t.Union[t.List[RawAPIItem], ModelNotImplemented]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.tournaments, team_id, max_items=max_items
        )


class AsyncTeams(BaseTeams[AsyncClient], t.Generic[APIResponseFormatT]):
    __slots__ = ()

    @t.overload
    async def get(self: AsyncTeams[Raw], team_id: _TeamID) -> RawAPIItem: ...

    @t.overload
    async def get(
        self: AsyncTeams[Model], team_id: _TeamID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def get(
        self, team_id: _TeamIDValidator
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(self.PATH / team_id, expect_item=True),
            ModelPlaceholder,
        )

    __call__ = get

    @te.deprecated(
        "`details` is deprecated and will be removed in a future release. "
        "Use `get` instead."
    )
    async def details(self, team_id: _TeamID) -> t.Any:
        return await self.get(team_id)

    @t.overload
    async def stats(
        self: AsyncTeams[Raw], team_id: _TeamID, game: GameID
    ) -> RawAPIItem: ...

    @t.overload
    async def stats(
        self: AsyncTeams[Model], team_id: _TeamID, game: GameID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def stats(
        self, team_id: _TeamIDValidator, game: GameID
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.PATH / team_id / "stats" / game, expect_item=True
            ),
            ModelPlaceholder,
        )

    @t.overload
    async def tournaments(
        self: AsyncTeams[Raw],
        team_id: _TeamID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def tournaments(
        self: AsyncTeams[Model],
        team_id: _TeamID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ModelNotImplemented: ...

    @validate_call
    async def tournaments(
        self,
        team_id: _TeamIDValidator,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.PATH / team_id / "tournaments",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @t.overload
    async def all_tournaments(
        self: AsyncTeams[Raw],
        team_id: _TeamID,
        *,
        max_items: MaxItemsType = pages(30),
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    async def all_tournaments(
        self: AsyncTeams[Model],
        team_id: _TeamID,
        *,
        max_items: MaxItemsType = pages(30),
    ) -> ModelNotImplemented: ...

    async def all_tournaments(
        self,
        team_id: _TeamIDValidator,
        *,
        max_items: MaxItemsType = pages(30),
    ) -> t.Union[t.List[RawAPIItem], ModelNotImplemented]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.tournaments, team_id, max_items=max_items
        )
