from __future__ import annotations

import typing as t
from abc import ABC
from uuid import UUID  # noqa: TCH003

from pydantic import Field, validate_call

from faceit._typing import (
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIItem,
    RawAPIPageResponse,
)
from faceit._utils import uuid_validator_alias
from faceit.constants import EventStatus, ExpandOption, GameID
from faceit.http import AsyncClient, SyncClient
from faceit.models import Championship, ItemPage

from .base import BaseResource, FaceitResourcePath

_championship_id_validator = uuid_validator_alias("championship_id")


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
        status: EventStatus = EventStatus.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def all(
        self: SyncChampionships[Model],
        game: GameID,
        status: EventStatus = EventStatus.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> ItemPage[Championship]: ...

    @validate_call
    def all(
        self,
        game: GameID,
        status: EventStatus = EventStatus.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> t.Union[RawAPIPageResponse, ItemPage[Championship]]:
        return self._validate_response(
            self._client.get(
                self.PATH,
                params=self.__class__._build_params(
                    game=game, status=status, offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[Championship],
        )

    @t.overload
    def get(
        self: SyncChampionships[Raw],
        championship_id: t.Union[str, UUID],
        expanded: ExpandOption = ExpandOption.NONE,
    ) -> RawAPIItem: ...

    @t.overload
    def get(
        self: SyncChampionships[Model],
        championship_id: t.Union[str, UUID],
        expanded: ExpandOption = ExpandOption.NONE,
    ) -> ModelNotImplemented: ...

    @_championship_id_validator
    @validate_call
    def get(
        self,
        championship_id: t.Union[str, UUID],
        expanded: ExpandOption = ExpandOption.NONE,
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        pass

    __call__ = get

    @t.overload
    def matches(
        self: SyncChampionships[Raw],
        championship_id: t.Union[str, UUID],
        status: EventStatus = EventStatus.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def matches(
        self: SyncChampionships[Model],
        championship_id: t.Union[str, UUID],
        status: EventStatus = EventStatus.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ModelNotImplemented: ...

    @_championship_id_validator
    @validate_call
    def matches(
        self,
        championship_id: t.Union[str, UUID],
        status: EventStatus = EventStatus.ALL,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        pass

    @t.overload
    def results(
        self: SyncChampionships[Raw],
        championship_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def results(
        self: SyncChampionships[Model],
        championship_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ModelNotImplemented: ...

    @_championship_id_validator
    @validate_call
    def results(
        self,
        championship_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        pass

    @t.overload
    def subscriptions(
        self: SyncChampionships[Raw],
        championship_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def subscriptions(
        self: SyncChampionships[Model],
        championship_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> ModelNotImplemented: ...

    @_championship_id_validator
    @validate_call
    def subscriptions(
        self,
        championship_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(10, ge=1, le=10),
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        pass


@t.final
class AsyncChampionships(
    BaseChampionships[AsyncClient], t.Generic[APIResponseFormatT]
):
    __slots__ = ()
