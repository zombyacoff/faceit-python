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
from faceit.constants import EventCategory, ExpandOption, GameID
from faceit.http import AsyncClient, SyncClient
from faceit.models import Championship, ItemPage

from ._base import BaseResource, FaceitResourcePath

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
    def all(
        self: SyncChampionships[Raw],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def all(
        self: SyncChampionships[Model],
        game: GameID,
        category: EventCategory = EventCategory.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> ItemPage[Championship]: ...

    @validate_call
    def all(
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
    def get(
        self: SyncChampionships[Raw],
        championship_id: _ChampionshipID,
        expanded: ExpandOption = ExpandOption.NONE,
    ) -> RawAPIItem: ...

    @t.overload
    def get(
        self: SyncChampionships[Model],
        championship_id: _ChampionshipID,
        expanded: ExpandOption = ExpandOption.NONE,
    ) -> ModelNotImplemented: ...

    @validate_call
    def get(
        self,
        championship_id: _ChampionshipIDValidator,
        expanded: ExpandOption = ExpandOption.NONE,
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(championship_id),
                params=self.__class__._build_params(expanded=expanded),
                expect_item=True,
            ),
            None,
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
            None,
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
            None,
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
            None,
        )


@t.final
class AsyncChampionships(
    BaseChampionships[AsyncClient], t.Generic[APIResponseFormatT]
):
    __slots__ = ()
