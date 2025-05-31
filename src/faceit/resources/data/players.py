# mypy: disable-error-code="no-any-return"
from __future__ import annotations

import logging
import typing
from abc import ABC
from warnings import warn

from pydantic import AfterValidator, Field, validate_call
from typing_extensions import Annotated, TypeAlias

from faceit.constants import GameID
from faceit.http import AsyncClient, SyncClient
from faceit.models import (
    BanEntry,
    CS2MatchPlayerStats,
    GeneralTeam,
    Hub,
    ItemPage,
    Match,
    Player,
    Tournament,
)
from faceit.models.players.match import AbstractMatchPlayerStats
from faceit.resources.base import (
    BaseResource,
    FaceitResourcePath,
    MappedValidatorConfig,
    ModelPlaceholder,
    RequestPayload,
)
from faceit.resources.pagination import MaxItems, MaxItemsType, pages
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
from faceit.utils import is_valid_uuid

from .helpers import validate_player_id, validate_player_id_or_nickname

_logger = logging.getLogger(__name__)

PlayerID: TypeAlias = ValidUUID
PlayerIDValidated: TypeAlias = Annotated[PlayerID, AfterValidator(validate_player_id)]
_PlayerIdentifier: TypeAlias = typing.Union[str, ValidUUID]
_PlayerIdentifierValidated: TypeAlias = Annotated[
    _PlayerIdentifier, AfterValidator(validate_player_id_or_nickname)
]


class BasePlayers(
    BaseResource[ClientT],
    ABC,
    resource_path=FaceitResourcePath.PLAYERS,
):
    __slots__ = ()

    _matches_stats_validator_cfg: typing.ClassVar = MappedValidatorConfig[
        GameID, AbstractMatchPlayerStats
    ](
        validator_map={
            GameID.CS2: CS2MatchPlayerStats,
            # TODO: Add other games (e.g. CSGO)
        },
        is_paged=True,
        key_name="game",
    )

    _matches_stats_timestamp_cfg: typing.ClassVar = BaseResource._timestamp_cfg(
        key="stats.Match Finished At", attr="match_finished_at"
    )
    _history_timestamp_cfg: typing.ClassVar = BaseResource._timestamp_cfg(
        key="finished_at", attr="finished_at"
    )

    def _process_get_request(
        self,
        player_lookup_key: typing.Any,
        game: typing.Optional[GameID],
        game_player_id: typing.Optional[str],
    ) -> RequestPayload:
        params = self.__class__._build_params(game=game, game_player_id=game_player_id)

        if player_lookup_key is None:
            if game is None or game_player_id is None:
                raise ValueError(
                    "When 'player_lookup_key' is not provided,"
                    "both 'game' AND 'game_player_id' must be specified"
                )
            _logger.debug(
                "Fetching player by game parameters: game=%s, game_player_id=%s",
                game,
                game_player_id,
            )
            return RequestPayload(endpoint=self.__class__.PATH, params=params)

        if game is not None or game_player_id is not None:
            warn(
                "When 'player_lookup_key' is provided, "
                "'game' and 'game_player_id' should not be specified. "
                "The value of 'player_lookup_key' will take precedence.",
                UserWarning,
                stacklevel=5,
            )

        if is_valid_uuid(player_lookup_key):
            _logger.debug("Fetching player by UUID: %s", player_lookup_key)
            return RequestPayload(
                endpoint=self.__class__.PATH / str(player_lookup_key), params=params
            )

        _logger.debug("Fetching player by nickname: %s", player_lookup_key)
        params["nickname"] = str(player_lookup_key)
        return RequestPayload(endpoint=self.__class__.PATH, params=params)


@typing.final
class SyncPlayers(BasePlayers[SyncClient], typing.Generic[APIResponseFormatT]):
    __slots__ = ()

    @typing.overload
    def get(
        self: SyncPlayers[Raw], player_lookup_key: _PlayerIdentifier
    ) -> RawAPIItem: ...

    @typing.overload
    def get(
        self: SyncPlayers[Raw], *, game: GameID, game_player_id: str
    ) -> RawAPIItem: ...

    @typing.overload
    def get(
        self: SyncPlayers[Model], player_lookup_key: _PlayerIdentifier
    ) -> Player: ...

    @typing.overload
    def get(
        self: SyncPlayers[Model], *, game: GameID, game_player_id: str
    ) -> Player: ...

    @validate_call
    def get(
        self,
        player_lookup_key: typing.Optional[_PlayerIdentifierValidated] = None,
        *,
        game: typing.Optional[GameID] = None,
        game_player_id: typing.Optional[str] = None,
    ) -> typing.Union[RawAPIItem, Player]:
        return self._validate_response(
            self._client.get(
                **self._process_get_request(player_lookup_key, game, game_player_id),
                expect_item=True,
            ),
            Player,
        )

    # This creates an alias allowing instances to be called directly like `resource(...)`
    # instead of `resource.get(...)`. While both forms are valid, using the explicit `.get()`
    # method is generally preferred for clarity. NOTE: The alias is maintained for convenience
    __call__ = get

    # Using `Field(...)` as default value rather than `Annotated[..., Field(...)]`
    # to expose constraints in IDE tooltips and improve developer experience
    @typing.overload
    def bans(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @typing.overload
    def bans(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[BanEntry]: ...

    @validate_call
    def bans(
        self,
        player_id: PlayerIDValidated,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> typing.Union[RawAPIPageResponse, ItemPage[BanEntry]]:
        return self._validate_response(
            self._client.get(
                # `player_id` is validated and normalized;
                # str() is only for mypy type narrowing.
                self.__class__.PATH / str(player_id) / "bans",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ItemPage[BanEntry],
        )

    @typing.overload
    def all_bans(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    def all_bans(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[BanEntry]: ...

    def all_bans(
        self, player_id: PlayerID, max_items: MaxItemsType = MaxItems.SAFE
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[BanEntry]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.bans, player_id, max_items=max_items
        )

    @typing.overload
    def matches_stats(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: typing.Optional[int] = None,
        to: typing.Optional[int] = None,
    ) -> RawAPIPageResponse: ...

    @typing.overload
    def matches_stats(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: typing.Optional[int] = None,
        to: typing.Optional[int] = None,
    ) -> ItemPage[AbstractMatchPlayerStats]: ...

    @validate_call
    def matches_stats(
        self,
        player_id: PlayerIDValidated,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: typing.Optional[int] = None,
        to: typing.Optional[int] = None,
    ) -> typing.Union[ItemPage[AbstractMatchPlayerStats], RawAPIPageResponse]:
        return self._process_response_with_mapped_validator(
            self._client.get(
                self.__class__.PATH / str(player_id) / "games" / game / "stats",
                params=self.__class__._build_params(
                    offset=offset, limit=limit, start=start, to=to
                ),
                expect_page=True,
            ),
            game,
            self.__class__._matches_stats_validator_cfg,
        )

    @typing.overload
    def all_matches_stats(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        max_items: MaxItemsType = pages(50),
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    def all_matches_stats(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        max_items: MaxItemsType = pages(50),
    ) -> ItemPage[AbstractMatchPlayerStats]: ...

    def all_matches_stats(
        self,
        player_id: PlayerID,
        game: GameID,
        max_items: MaxItemsType = pages(50),
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[AbstractMatchPlayerStats]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.matches_stats,
            player_id,
            game,
            max_items=max_items,
            unix=self.__class__._matches_stats_timestamp_cfg,
        )

    @typing.overload
    def history(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: typing.Optional[int] = None,
        to: typing.Optional[int] = None,
    ) -> RawAPIPageResponse: ...

    @typing.overload
    def history(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: typing.Optional[int] = None,
        to: typing.Optional[int] = None,
    ) -> ItemPage[Match]: ...

    @validate_call
    def history(
        self,
        player_id: PlayerIDValidated,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: typing.Optional[int] = None,
        to: typing.Optional[int] = None,
    ) -> typing.Union[RawAPIPageResponse, ItemPage[Match]]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(player_id) / "history",
                params=self.__class__._build_params(
                    game=game, offset=offset, limit=limit, start=start, to=to
                ),
                expect_page=True,
            ),
            ItemPage[Match],
        )

    @typing.overload
    def all_history(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        max_items: MaxItemsType = pages(50),
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    def all_history(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        max_items: MaxItemsType = pages(50),
    ) -> ItemPage[Match]: ...

    def all_history(
        self,
        player_id: PlayerID,
        game: GameID,
        max_items: MaxItemsType = pages(50),
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[Match]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.history,
            player_id,
            game,
            max_items=max_items,
            unix=self.__class__._history_timestamp_cfg,
        )

    @typing.overload
    def hubs(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> RawAPIPageResponse: ...

    @typing.overload
    def hubs(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> ItemPage[Hub]: ...

    @validate_call
    def hubs(
        self,
        player_id: PlayerIDValidated,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> typing.Union[RawAPIPageResponse, ItemPage[Hub]]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(player_id) / "hubs",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ItemPage[Hub],
        )

    @typing.overload
    def all_hubs(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    def all_hubs(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[Hub]: ...

    def all_hubs(
        self, player_id: PlayerID, max_items: MaxItemsType = MaxItems.SAFE
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[Hub]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.hubs, player_id, max_items=max_items
        )

    @typing.overload
    def stats(
        self: SyncPlayers[Raw], player_id: PlayerID, game: GameID
    ) -> RawAPIPageResponse: ...

    @typing.overload
    def stats(
        self: SyncPlayers[Model], player_id: PlayerID, game: GameID
    ) -> ModelNotImplemented: ...

    @validate_call
    def stats(
        self, player_id: PlayerIDValidated, game: GameID
    ) -> typing.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(player_id) / "stats" / game,
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @typing.overload
    def teams(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @typing.overload
    def teams(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[GeneralTeam]: ...

    @validate_call
    def teams(
        self,
        player_id: PlayerIDValidated,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> typing.Union[RawAPIPageResponse, ItemPage[GeneralTeam]]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(player_id) / "teams",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ItemPage[GeneralTeam],
        )

    @typing.overload
    def all_teams(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    def all_teams(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[GeneralTeam]: ...

    def all_teams(
        self, player_id: PlayerID, max_items: MaxItemsType = MaxItems.SAFE
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[GeneralTeam]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.teams, player_id, max_items=max_items
        )

    @typing.overload
    def tournaments(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @typing.overload
    def tournaments(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[Tournament]: ...

    @validate_call
    def tournaments(
        self,
        player_id: PlayerIDValidated,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> typing.Union[RawAPIPageResponse, ItemPage[Tournament]]:
        return self._validate_response(
            self._client.get(
                self.__class__.PATH / str(player_id) / "tournaments",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ItemPage[Tournament],
        )

    @typing.overload
    def all_tournaments(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    def all_tournaments(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[Tournament]: ...

    def all_tournaments(
        self, player_id: PlayerID, max_items: MaxItemsType = MaxItems.SAFE
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[Tournament]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.tournaments, player_id, max_items=max_items
        )


@typing.final
class AsyncPlayers(BasePlayers[AsyncClient], typing.Generic[APIResponseFormatT]):
    __slots__ = ()

    @typing.overload
    async def get(
        self: AsyncPlayers[Raw], player_lookup_key: _PlayerIdentifier
    ) -> RawAPIItem: ...

    @typing.overload
    async def get(
        self: AsyncPlayers[Raw], *, game: GameID, game_player_id: str
    ) -> RawAPIItem: ...

    @typing.overload
    async def get(
        self: AsyncPlayers[Model], player_lookup_key: _PlayerIdentifier
    ) -> Player: ...

    @typing.overload
    async def get(
        self: AsyncPlayers[Model], *, game: GameID, game_player_id: str
    ) -> Player: ...

    @validate_call
    async def get(
        self,
        player_lookup_key: typing.Optional[_PlayerIdentifierValidated] = None,
        *,
        game: typing.Optional[GameID] = None,
        game_player_id: typing.Optional[str] = None,
    ) -> typing.Union[RawAPIItem, Player]:
        return self._validate_response(
            await self._client.get(
                **self._process_get_request(player_lookup_key, game, game_player_id),
                expect_item=True,
            ),
            Player,
        )

    __call__ = get

    @typing.overload
    async def bans(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @typing.overload
    async def bans(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[BanEntry]: ...

    @validate_call
    async def bans(
        self,
        player_id: PlayerIDValidated,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> typing.Union[RawAPIPageResponse, ItemPage[BanEntry]]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(player_id) / "bans",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ItemPage[BanEntry],
        )

    @typing.overload
    async def all_bans(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    async def all_bans(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[BanEntry]: ...

    async def all_bans(
        self, player_id: PlayerID, max_items: MaxItemsType = MaxItems.SAFE
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[BanEntry]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.bans, player_id, max_items=max_items
        )

    @typing.overload
    async def matches_stats(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: typing.Optional[int] = None,
        to: typing.Optional[int] = None,
    ) -> RawAPIPageResponse: ...

    @typing.overload
    async def matches_stats(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: typing.Optional[int] = None,
        to: typing.Optional[int] = None,
    ) -> ItemPage[AbstractMatchPlayerStats]: ...

    @validate_call
    async def matches_stats(
        self,
        player_id: PlayerIDValidated,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: typing.Optional[int] = None,
        to: typing.Optional[int] = None,
    ) -> typing.Union[RawAPIPageResponse, ItemPage[AbstractMatchPlayerStats]]:
        return self._process_response_with_mapped_validator(
            await self._client.get(
                self.__class__.PATH / str(player_id) / "games" / game / "stats",
                params=self.__class__._build_params(
                    offset=offset, limit=limit, start=start, to=to
                ),
                expect_page=True,
            ),
            game,
            self.__class__._matches_stats_validator_cfg,
        )

    @typing.overload
    async def all_matches_stats(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        max_items: MaxItemsType = pages(50),
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    async def all_matches_stats(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        max_items: MaxItemsType = pages(50),
    ) -> ItemPage[AbstractMatchPlayerStats]: ...

    async def all_matches_stats(
        self,
        player_id: PlayerID,
        game: GameID,
        max_items: MaxItemsType = pages(50),
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[AbstractMatchPlayerStats]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.matches_stats,
            player_id,
            game,
            max_items=max_items,
            unix=self.__class__._matches_stats_timestamp_cfg,
        )

    @typing.overload
    async def history(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: typing.Optional[int] = None,
        to: typing.Optional[int] = None,
    ) -> RawAPIPageResponse: ...

    @typing.overload
    async def history(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: typing.Optional[int] = None,
        to: typing.Optional[int] = None,
    ) -> ItemPage[Match]: ...

    @validate_call
    async def history(
        self,
        player_id: PlayerIDValidated,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: typing.Optional[int] = None,
        to: typing.Optional[int] = None,
    ) -> typing.Union[RawAPIPageResponse, ItemPage[Match]]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(player_id) / "history",
                params=self.__class__._build_params(
                    game=game, offset=offset, limit=limit, start=start, to=to
                ),
                expect_page=True,
            ),
            ItemPage[Match],
        )

    @typing.overload
    async def all_history(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        max_items: MaxItemsType = pages(50),
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    async def all_history(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        max_items: MaxItemsType = pages(50),
    ) -> ItemPage[Match]: ...

    async def all_history(
        self,
        player_id: PlayerID,
        game: GameID,
        max_items: MaxItemsType = pages(50),
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[Match]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.history,
            player_id,
            game,
            max_items=max_items,
            unix=self.__class__._history_timestamp_cfg,
        )

    @typing.overload
    async def hubs(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> RawAPIPageResponse: ...

    @typing.overload
    async def hubs(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> ItemPage[Hub]: ...

    @validate_call
    async def hubs(
        self,
        player_id: PlayerIDValidated,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> typing.Union[RawAPIPageResponse, ItemPage[Hub]]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(player_id) / "hubs",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ItemPage[Hub],
        )

    @typing.overload
    async def all_hubs(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    async def all_hubs(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[Hub]: ...

    async def all_hubs(
        self, player_id: PlayerID, max_items: MaxItemsType = MaxItems.SAFE
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[Hub]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.hubs, player_id, max_items=max_items
        )

    @typing.overload
    async def stats(
        self: AsyncPlayers[Raw], player_id: PlayerID, game: GameID
    ) -> RawAPIPageResponse: ...

    @typing.overload
    async def stats(
        self: AsyncPlayers[Model], player_id: PlayerID, game: GameID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def stats(
        self, player_id: PlayerIDValidated, game: GameID
    ) -> typing.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(player_id) / "stats" / game,
                expect_page=True,
            ),
            ModelPlaceholder,
        )

    @typing.overload
    async def teams(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @typing.overload
    async def teams(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[GeneralTeam]: ...

    @validate_call
    async def teams(
        self,
        player_id: PlayerIDValidated,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> typing.Union[RawAPIPageResponse, ItemPage[GeneralTeam]]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(player_id) / "teams",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ItemPage[GeneralTeam],
        )

    @typing.overload
    async def all_teams(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    async def all_teams(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[GeneralTeam]: ...

    async def all_teams(
        self, player_id: PlayerID, max_items: MaxItemsType = MaxItems.SAFE
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[GeneralTeam]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.teams, player_id, max_items=max_items
        )

    @typing.overload
    async def tournaments(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @typing.overload
    async def tournaments(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[Tournament]: ...

    @validate_call
    async def tournaments(
        self,
        player_id: PlayerIDValidated,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> typing.Union[RawAPIPageResponse, ItemPage[Tournament]]:
        return self._validate_response(
            await self._client.get(
                self.__class__.PATH / str(player_id) / "tournaments",
                params=self.__class__._build_params(offset=offset, limit=limit),
                expect_page=True,
            ),
            ItemPage[Tournament],
        )

    @typing.overload
    async def all_tournaments(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> typing.List[RawAPIItem]: ...

    @typing.overload
    async def all_tournaments(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[Tournament]: ...

    async def all_tournaments(
        self, player_id: PlayerID, max_items: MaxItemsType = MaxItems.SAFE
    ) -> typing.Union[typing.List[RawAPIItem], ItemPage[Tournament]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.tournaments, player_id, max_items=max_items
        )
