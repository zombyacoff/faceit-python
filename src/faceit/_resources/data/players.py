from __future__ import annotations

import logging
import sys
import typing as t
from abc import ABC
from warnings import warn

from pydantic import AfterValidator, Field, validate_call

from faceit._resources.base import (
    BaseResource,
    FaceitResourcePath,
    MappedValidatorConfig,
    ModelPlaceholder,
    RequestPayload,
)
from faceit._resources.pagination import MaxItems, MaxItemsType, MaxPages
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
from faceit._utils import create_uuid_validator, is_valid_uuid
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
from faceit.models._player import AbstractMatchPlayerStats

_logger = logging.getLogger(__name__)

# Type alias for player ID.
# Improves code self-documentation and keeps resource modules consistent.
# Allows flexible substitution (e.g., `ValidUUID`, `str`) as in other modules.
PlayerID: TypeAlias = ValidUUID
# Pydantic validator for `player_id`.
# Centralizes validation and normalization at the parameter level,
# so resource methods always receive a valid, normalized ID.
# Also matches `validate_call` usage for pagination params, reducing boilerplate.
PlayerIDValidator: TypeAlias = Annotated[
    PlayerID,
    AfterValidator(create_uuid_validator(arg_name="player identifier")),
]
# Alias for FACEIT ID (`UUID`, `bytes`, `str`) or nickname (`str`).
# Used for clarity when both forms are accepted by resource methods.
NicknameOrPlayerID: TypeAlias = t.Union[str, ValidUUID]


class BasePlayers(
    BaseResource[ClientT],
    ABC,
    resource_path=FaceitResourcePath.PLAYERS,
):
    __slots__ = ()

    _matches_stats_validator_cfg: t.ClassVar = (
        MappedValidatorConfig[GameID, AbstractMatchPlayerStats]
        if sys.version_info >= (3, 9)
        else MappedValidatorConfig
    )(
        validator_map={
            GameID.CS2: CS2MatchPlayerStats,
            # TODO: Add other games (e.g. CSGO)
        },
        is_paged=True,
        key_name="game",
    )

    _matches_stats_timestamp_cfg: t.ClassVar = BaseResource._timestamp_cfg(
        key="stats.Match Finished At", attr="match_finished_at"
    )
    _history_timestamp_cfg: t.ClassVar = BaseResource._timestamp_cfg(
        key="finished_at", attr="finished_at"
    )

    def _process_get_request(
        self,
        player_lookup_key: t.Optional[NicknameOrPlayerID],
        game: t.Optional[GameID],
        game_player_id: t.Optional[str],
        /,
    ) -> RequestPayload:
        params = self.__class__._build_params(
            game=game, game_player_id=game_player_id
        )

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
            return RequestPayload(endpoint=self.PATH, params=params)

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
                endpoint=self.PATH / str(player_lookup_key), params=params
            )

        _logger.debug("Fetching player by nickname: %s", player_lookup_key)
        params["nickname"] = str(player_lookup_key)
        return RequestPayload(endpoint=self.PATH, params=params)


@t.final
class SyncPlayers(BasePlayers[SyncClient], t.Generic[APIResponseFormatT]):
    __slots__ = ()

    @t.overload
    def get(
        self: SyncPlayers[Raw], player_lookup_key: NicknameOrPlayerID
    ) -> RawAPIItem: ...

    @t.overload
    def get(
        self: SyncPlayers[Raw], *, game: GameID, game_player_id: str
    ) -> RawAPIItem: ...

    @t.overload
    def get(
        self: SyncPlayers[Model], player_lookup_key: NicknameOrPlayerID
    ) -> Player: ...

    @t.overload
    def get(
        self: SyncPlayers[Model], *, game: GameID, game_player_id: str
    ) -> Player: ...

    @validate_call
    def get(
        self,
        player_lookup_key: t.Optional[NicknameOrPlayerID] = None,
        *,
        game: t.Optional[GameID] = None,
        game_player_id: t.Optional[str] = None,
    ) -> t.Union[RawAPIItem, Player]:
        """
        Fetch player data either by identifier or by game-specific parameters.

        Args:
            player_lookup_key: Player's FACEIT UUID or nickname
            game: Game identifier (required if using game_player_id)
            game_player_id: Game-specific player ID (requires game parameter)

        Returns:
            Player model or raw dict depending on client configuration

        Examples::

            # Get player by nickname
            player = faceit.resources.players.get("s1mple")
            # Get player by UUID (string format works too)
            player = faceit.resources.players.get("ac71ba3c-d3d4-45e7-8be2-26aa3986867d")
            # Get player by game ID and game player ID
            player = faceit.resources.players.get(game=GameID.CS2, game_player_id="76561198034202275")
            assert isinstance(player.id, FaceitID)
            assert str(player.id) == "ac71ba3c-d3d4-45e7-8be2-26aa3986867d"

            # Get raw player data (returns `dict`)
            player_data = faceit.resources.raw_players.get("s1mple")
            assert isinstance(player_data, dict)
            assert player_data["nickname"] == "s1mple"
        """
        return self._validate_response(
            self._client.get(
                **self._process_get_request(
                    player_lookup_key, game, game_player_id
                ),
                expect_item=True,
            ),
            Player,
        )

    # This creates an alias allowing instances to be called directly like `resource(...)`
    # instead of `resource.get(...)`. While both forms are valid, using the explicit `.get()`
    # method is generally preferred for clarity. NOTE: The alias is maintained for convenience
    __call__ = get

    # Using `Field(...)` as default value rather than `Annotated[T, Field(...)]`
    # to expose constraints in IDE tooltips and improve developer experience
    @t.overload
    def bans(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
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
        player_id: PlayerIDValidator,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ItemPage[BanEntry]]:
        return self._validate_response(
            self._client.get(
                # `player_id` is validated and normalized;
                # str() is only for mypy type narrowing.
                self.PATH / str(player_id) / "bans",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[BanEntry],
        )

    @t.overload
    def all_bans(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    def all_bans(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[BanEntry]: ...

    def all_bans(
        self, player_id: PlayerID, *, max_items: MaxItemsType = MaxItems.SAFE
    ) -> t.Union[t.List[RawAPIItem], ItemPage[BanEntry]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.bans, player_id, max_items=max_items
        )

    @t.overload
    def matches_stats(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> RawAPIPageResponse: ...

    @t.overload
    def matches_stats(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> ItemPage[AbstractMatchPlayerStats]: ...

    @validate_call
    def matches_stats(
        self,
        player_id: PlayerIDValidator,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> t.Union[ItemPage[AbstractMatchPlayerStats], RawAPIPageResponse]:
        return self._process_response_with_mapped_validator(
            self._client.get(
                self.PATH / str(player_id) / "games" / game / "stats",
                params=self.__class__._build_params(
                    offset=offset, limit=limit, start=start, to=to
                ),
                expect_page=True,
            ),
            game,
            **self.__class__._matches_stats_validator_cfg,
        )

    @t.overload
    def all_matches_stats(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        *,
        max_items: MaxItemsType = MaxPages(50),
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    def all_matches_stats(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        *,
        max_items: MaxItemsType = MaxPages(50),
    ) -> ItemPage[AbstractMatchPlayerStats]: ...

    def all_matches_stats(
        self,
        player_id: PlayerID,
        game: GameID,
        *,
        max_items: MaxItemsType = MaxPages(50),
    ) -> t.Union[t.List[RawAPIItem], ItemPage[AbstractMatchPlayerStats]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.matches_stats,
            player_id,
            game,
            max_items=max_items,
            unix=self.__class__._matches_stats_timestamp_cfg,
        )

    @t.overload
    def history(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> RawAPIPageResponse: ...

    @t.overload
    def history(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> ItemPage[Match]: ...

    @validate_call
    def history(
        self,
        player_id: PlayerIDValidator,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> t.Union[RawAPIPageResponse, ItemPage[Match]]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(player_id) / "history",
                params=self.__class__._build_params(
                    game=game, offset=offset, limit=limit, start=start, to=to
                ),
                expect_page=True,
            ),
            ItemPage[Match],
        )

    @t.overload
    def all_history(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        *,
        max_items: MaxItemsType = MaxPages(50),
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    def all_history(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        *,
        max_items: MaxItemsType = MaxPages(50),
    ) -> ItemPage[Match]: ...

    def all_history(
        self,
        player_id: PlayerID,
        game: GameID,
        *,
        max_items: MaxItemsType = MaxPages(50),
    ) -> t.Union[t.List[RawAPIItem], ItemPage[Match]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.history,
            player_id,
            game,
            max_items=max_items,
            unix=self.__class__._history_timestamp_cfg,
        )

    @t.overload
    def hubs(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> RawAPIPageResponse: ...

    @t.overload
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
        player_id: PlayerIDValidator,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> t.Union[RawAPIPageResponse, ItemPage[Hub]]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(player_id) / "hubs",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[Hub],
        )

    @t.overload
    def all_hubs(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    def all_hubs(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[Hub]: ...

    def all_hubs(
        self, player_id: PlayerID, *, max_items: MaxItemsType = MaxItems.SAFE
    ) -> t.Union[t.List[RawAPIItem], ItemPage[Hub]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.hubs, player_id, max_items=max_items
        )

    @t.overload
    def stats(
        self: SyncPlayers[Raw], player_id: PlayerID, game: GameID
    ) -> RawAPIPageResponse: ...

    @t.overload
    def stats(
        self: SyncPlayers[Model], player_id: PlayerID, game: GameID
    ) -> ModelNotImplemented: ...

    @validate_call
    def stats(
        self, player_id: PlayerIDValidator, game: GameID
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(player_id) / "stats" / game, expect_page=True
            ),
            ModelPlaceholder,
        )

    @t.overload
    def teams(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
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
        player_id: PlayerIDValidator,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ItemPage[GeneralTeam]]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(player_id) / "teams",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[GeneralTeam],
        )

    @t.overload
    def all_teams(
        self: SyncPlayers[Raw], player_id: PlayerID
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    def all_teams(
        self: SyncPlayers[Model], player_id: PlayerID
    ) -> ItemPage[GeneralTeam]: ...

    def all_teams(
        self, player_id: PlayerID
    ) -> t.Union[t.List[RawAPIItem], ItemPage[GeneralTeam]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.teams, player_id
        )

    @t.overload
    def tournaments(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
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
        player_id: PlayerIDValidator,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ItemPage[Tournament]]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(player_id) / "tournaments",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[Tournament],
        )

    @t.overload
    def all_tournaments(
        self: SyncPlayers[Raw],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    def all_tournaments(
        self: SyncPlayers[Model],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[Tournament]: ...

    def all_tournaments(
        self,
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> t.Union[t.List[RawAPIItem], ItemPage[Tournament]]:
        return self.__class__._sync_page_iterator.gather_pages(
            self.tournaments, player_id, max_items=max_items
        )


@t.final
class AsyncPlayers(BasePlayers[AsyncClient], t.Generic[APIResponseFormatT]):
    __slots__ = ()

    @t.overload
    async def get(
        self: AsyncPlayers[Raw], player_lookup_key: NicknameOrPlayerID
    ) -> RawAPIItem: ...

    @t.overload
    async def get(
        self: AsyncPlayers[Raw], *, game: GameID, game_player_id: str
    ) -> RawAPIItem: ...

    @t.overload
    async def get(
        self: AsyncPlayers[Model], player_lookup_key: NicknameOrPlayerID
    ) -> Player: ...

    @t.overload
    async def get(
        self: AsyncPlayers[Model], *, game: GameID, game_player_id: str
    ) -> Player: ...

    @validate_call
    async def get(
        self,
        player_lookup_key: t.Optional[NicknameOrPlayerID] = None,
        *,
        game: t.Optional[GameID] = None,
        game_player_id: t.Optional[str] = None,
    ) -> t.Union[RawAPIItem, Player]:
        """
        Fetch player data either by identifier or by game-specific parameters asynchronously.

        Args:
            player_lookup_key: Player's FACEIT UUID or nickname
            game: Game identifier (required if using game_player_id)
            game_player_id: Game-specific player ID (requires game parameter)

        Returns:
            Player model or raw dict depending on client configuration

        Examples::

            # Get player by nickname
            player = await faceit.resources.players.get("s1mple")
            # Get player by UUID (string format works too)
            player = await faceit.resources.players.get("ac71ba3c-d3d4-45e7-8be2-26aa3986867d")
            # Get player by game ID and game player ID
            player = await faceit.resources.players.get(game=GameID.CS2, game_player_id="76561198034202275")
            assert isinstance(player.id, FaceitID)
            assert str(player.id) == "ac71ba3c-d3d4-45e7-8be2-26aa3986867d"

            # Get raw player data (returns `dict`)
            player_data = await faceit.resources.raw_players.get("s1mple")
            assert isinstance(player_data, dict)
            assert player_data["nickname"] == "s1mple"
        """
        return self._validate_response(
            await self._client.get(
                **self._process_get_request(
                    player_lookup_key, game, game_player_id
                ),
                expect_item=True,
            ),
            Player,
        )

    __call__ = get

    @t.overload
    async def bans(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
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
        player_id: PlayerIDValidator,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ItemPage[BanEntry]]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(player_id) / "bans",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[BanEntry],
        )

    @t.overload
    async def all_bans(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    async def all_bans(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[BanEntry]: ...

    async def all_bans(
        self,
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> t.Union[t.List[RawAPIItem], ItemPage[BanEntry]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.bans, player_id, max_items=max_items
        )

    @t.overload
    async def matches_stats(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def matches_stats(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> ItemPage[AbstractMatchPlayerStats]: ...

    @validate_call
    async def matches_stats(
        self,
        player_id: PlayerIDValidator,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> t.Union[RawAPIPageResponse, ItemPage[AbstractMatchPlayerStats]]:
        return self._process_response_with_mapped_validator(
            await self._client.get(
                self.PATH / str(player_id) / "games" / game / "stats",
                params=self.__class__._build_params(
                    offset=offset, limit=limit, start=start, to=to
                ),
                expect_page=True,
            ),
            game,
            **self.__class__._matches_stats_validator_cfg,
        )

    @t.overload
    async def all_matches_stats(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        *,
        max_items: MaxItemsType = MaxPages(50),
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    async def all_matches_stats(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        *,
        max_items: MaxItemsType = MaxPages(50),
    ) -> ItemPage[AbstractMatchPlayerStats]: ...

    async def all_matches_stats(
        self,
        player_id: PlayerID,
        game: GameID,
        *,
        max_items: MaxItemsType = MaxPages(50),
    ) -> t.Union[t.List[RawAPIItem], ItemPage[AbstractMatchPlayerStats]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.matches_stats,
            player_id,
            game,
            max_items=max_items,
            unix=self.__class__._matches_stats_timestamp_cfg,
        )

    @t.overload
    async def history(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def history(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> ItemPage[Match]: ...

    @validate_call
    async def history(
        self,
        player_id: PlayerIDValidator,
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> t.Union[RawAPIPageResponse, ItemPage[Match]]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(player_id) / "history",
                params=self.__class__._build_params(
                    game=game, offset=offset, limit=limit, start=start, to=to
                ),
                expect_page=True,
            ),
            ItemPage[Match],
        )

    @t.overload
    async def all_history(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        game: GameID,
        *,
        max_items: MaxItemsType = MaxPages(50),
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    async def all_history(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        game: GameID,
        *,
        max_items: MaxItemsType = MaxPages(50),
    ) -> ItemPage[Match]: ...

    async def all_history(
        self,
        player_id: PlayerID,
        game: GameID,
        *,
        max_items: MaxItemsType = MaxPages(50),
    ) -> t.Union[t.List[RawAPIItem], ItemPage[Match]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.history,
            player_id,
            game,
            max_items=max_items,
            unix=self.__class__._history_timestamp_cfg,
        )

    @t.overload
    async def hubs(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> RawAPIPageResponse: ...

    @t.overload
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
        player_id: PlayerIDValidator,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> t.Union[RawAPIPageResponse, ItemPage[Hub]]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(player_id) / "hubs",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[Hub],
        )

    @t.overload
    async def all_hubs(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    async def all_hubs(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[Hub]: ...

    async def all_hubs(
        self,
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> t.Union[t.List[RawAPIItem], ItemPage[Hub]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.hubs, player_id, max_items=max_items
        )

    @t.overload
    async def stats(
        self: AsyncPlayers[Raw], player_id: PlayerID, game: GameID
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def stats(
        self: AsyncPlayers[Model], player_id: PlayerID, game: GameID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def stats(
        self, player_id: PlayerIDValidator, game: GameID
    ) -> t.Union[RawAPIPageResponse, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(player_id) / "stats" / game, expect_page=True
            ),
            ModelPlaceholder,
        )

    @t.overload
    async def teams(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
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
        player_id: PlayerIDValidator,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ItemPage[GeneralTeam]]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(player_id) / "teams",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[GeneralTeam],
        )

    @t.overload
    async def all_teams(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    async def all_teams(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[GeneralTeam]: ...

    async def all_teams(
        self,
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> t.Union[t.List[RawAPIItem], ItemPage[GeneralTeam]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.teams, player_id, max_items=max_items
        )

    @t.overload
    async def tournaments(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
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
        player_id: PlayerIDValidator,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ItemPage[Tournament]]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(player_id) / "tournaments",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[Tournament],
        )

    @t.overload
    async def all_tournaments(
        self: AsyncPlayers[Raw],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    async def all_tournaments(
        self: AsyncPlayers[Model],
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> ItemPage[Tournament]: ...

    async def all_tournaments(
        self,
        player_id: PlayerID,
        *,
        max_items: MaxItemsType = MaxItems.SAFE,
    ) -> t.Union[t.List[RawAPIItem], ItemPage[Tournament]]:
        return await self.__class__._async_page_iterator.gather_pages(
            self.tournaments, player_id, max_items=max_items
        )
