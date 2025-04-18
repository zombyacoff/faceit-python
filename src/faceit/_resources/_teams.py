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
)
from faceit.constants import GameID  # noqa: TCH001
from faceit.http import AsyncClient, SyncClient

from ._base import BaseResource, FaceitResourcePath, ModelPlaceholder

_TeamID: TypeAlias = str
_TeamIDValidator: TypeAlias = Annotated[
    _TeamID, AfterValidator(lambda x: x)  # TODO: Validation function
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
    def details(self: SyncTeams[Raw], team_id: _TeamID) -> RawAPIItem: ...

    @t.overload
    def details(
        self: SyncTeams[Model], team_id: _TeamID
    ) -> ModelNotImplemented: ...

    @validate_call
    def details(
        self, team_id: _TeamIDValidator
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(self.PATH / team_id, expect_item=True),
            ModelPlaceholder,
        )

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


class AsyncTeams(BaseTeams[AsyncClient], t.Generic[APIResponseFormatT]):
    __slots__ = ()
