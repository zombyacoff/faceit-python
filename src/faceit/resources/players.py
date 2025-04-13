from __future__ import annotations

import logging
import typing as t
import warnings
from abc import ABC
from uuid import UUID  # noqa: TCH003

from pydantic import Field, validate_call

from faceit._types import (
    APIResponseFormatT,
    ClientT,
    Model,
    ParamSpec,
    Raw,
    RawAPIItem,
    RawAPIPageResponse,
)
from faceit._utils import is_valid_uuid, validate_uuid_args
from faceit.constants import GameID
from faceit.http import AsyncClient, SyncClient
from faceit.models import (
    BanEntry,
    BaseMatchPlayerStats,
    CS2MatchPlayerStats,
    GeneralTeam,
    Hub,
    ItemPage,
    Match,
    Player,
    Tournament,
)

from .base import BaseResource, FaceitResourcePath, RequestPayload

if t.TYPE_CHECKING:
    _T = t.TypeVar("_T")
    _P = ParamSpec("_P")

_logger = logging.getLogger(__name__)


def _validate_player_id(func: t.Callable[_P, _T]) -> t.Callable[_P, _T]:
    return validate_uuid_args("player_id")(func)


class BasePlayers(BaseResource[ClientT], ABC):
    _resource_path = FaceitResourcePath.PLAYERS
    _match_stats_model_types: t.Dict[GameID, t.Type[BaseMatchPlayerStats]] = {
        GameID.CS2: CS2MatchPlayerStats,
        # TODO: Add other games (e.g. CSGO)
    }

    def _process_get_request(
        self,
        identifier: t.Optional[t.Union[str, UUID]],
        game: t.Optional[GameID],
        game_player_id: t.Optional[str],
        /,
    ) -> RequestPayload:
        params = self.__class__._build_params(
            game=game, game_player_id=game_player_id
        )

        if identifier is None:
            if game is None or game_player_id is None:
                raise ValueError(
                    "When 'identifier' is not provided,"
                    "both 'game' AND 'game_player_id' must be specified"
                )
            _logger.info(
                "Fetching player by game parameters: game=%s, game_player_id=%s",
                game,
                game_player_id,
            )
            return RequestPayload(endpoint=self.path, params=params)

        if game is not None or game_player_id is not None:
            warnings.warn(
                "When 'identifier' is provided, "
                "'game' and 'game_player_id' should not be specified",
                UserWarning,
                stacklevel=3,
            )

        if is_valid_uuid(identifier):
            _logger.info("Fetching player by UUID: %s", identifier)
            return RequestPayload(
                endpoint=self.path / str(identifier), params=params
            )

        _logger.info("Fetching player by nickname: %s", identifier)
        params["nickname"] = str(identifier)
        return RequestPayload(endpoint=self.path, params=params)

    # TODO: Выделить данную логику в универсальный метод класса,
    # так как весьма вероятно, что она будет использоваться в других ресурсах
    def _process_matches_stats_response(
        self, response: RawAPIPageResponse, game: GameID, /
    ) -> t.Union[ItemPage, RawAPIPageResponse]:
        _logger.debug("Processing match stats response for game: %s", game)

        validator = self._match_stats_model_types.get(game)
        if validator is not None:
            # Suppressing type checking warning because we're using a
            # dynamic runtime subscript `ItemPage` is being subscripted
            # with a variable (`validator`) which mypy cannot statically verify
            return self._validate_response(response, ItemPage[validator])  # type: ignore[valid-type]

        warnings.warn(
            f"No model defined for game '{game}'. "
            "Consider using the raw response",
            UserWarning,
            stacklevel=3,
        )
        return response


@t.final
class SyncPlayers(BasePlayers[SyncClient], t.Generic[APIResponseFormatT]):
    @t.overload
    def get(
        self: SyncPlayers[Raw], identifier: t.Union[str, UUID]
    ) -> RawAPIItem: ...

    @t.overload
    def get(
        self: SyncPlayers[Raw], *, game: GameID, game_player_id: str
    ) -> RawAPIItem: ...

    @t.overload
    def get(
        self: SyncPlayers[Model], identifier: t.Union[str, UUID]
    ) -> Player: ...

    @t.overload
    def get(
        self: SyncPlayers[Model], *, game: GameID, game_player_id: str
    ) -> Player: ...

    def get(
        self,
        identifier: t.Optional[t.Union[str, UUID]] = None,
        *,
        game: t.Optional[GameID] = None,
        game_player_id: t.Optional[str] = None,
    ) -> t.Union[RawAPIItem, Player]:
        """Fetch player data either by identifier or by game-specific parameters.

        Args:
            identifier: Player's FACEIT UUID or nickname
            game: Game identifier (required if using game_player_id)
            game_player_id: Game-specific player ID (requires game parameter)

        Returns:
            Player model or raw dict depending on client configuration

        Examples:
            ```python
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
            ```
        """
        return self._validate_response(
            self._client.get(
                **self._process_get_request(identifier, game, game_player_id),
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
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def bans(
        self: SyncPlayers[Model],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[BanEntry]: ...

    @_validate_player_id
    @validate_call
    def bans(
        self,
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ItemPage[BanEntry]]:
        return self._validate_response(
            self._client.get(
                self.path / str(player_id) / "bans",  # `str(...)` for `UUID`
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[BanEntry],
        )

    @t.overload
    def all_bans(
        self: SyncPlayers[Raw], player_id: t.Union[str, UUID]
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    def all_bans(
        self: SyncPlayers[Model], player_id: t.Union[str, UUID]
    ) -> ItemPage[BanEntry]: ...

    def all_bans(
        self, player_id: t.Union[str, UUID]
    ) -> t.Union[ItemPage[BanEntry], t.List[RawAPIItem]]:
        # Mypy can't infer return type when passing generic method to higher-order function
        # Runtime behavior is correct, but static typing is limited by generic invariance
        return self.__class__._sync_page_iterator.collect(self.bans, player_id)  # type: ignore[misc]

    @t.overload
    def matches_stats(
        self: SyncPlayers[Raw],
        player_id: t.Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> RawAPIPageResponse: ...

    # NOTE: Currently, there is only one model for validating game
    # statistics - so we return only it. In the future, when expanding
    # the models, we will need to devise a solution for the return value
    @t.overload
    def matches_stats(
        self: SyncPlayers[Model],
        player_id: t.Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> ItemPage[CS2MatchPlayerStats]: ...

    @_validate_player_id
    @validate_call
    def matches_stats(
        self,
        player_id: t.Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> t.Union[ItemPage[CS2MatchPlayerStats], RawAPIPageResponse]:
        return self._process_matches_stats_response(
            self._client.get(
                self.path / str(player_id) / "games" / game / "stats",
                params=self.__class__._build_params(
                    offset=offset, limit=limit, start=start, to=to
                ),
                expect_page=True,
            ),
            game,  # `game` parameter is used to select the appropriate model for validation
        )

    @t.overload
    def all_matches_stats(
        self: SyncPlayers[Raw], player_id: t.Union[str, UUID], game: GameID
    ) -> t.List[RawAPIItem]: ...

    @t.overload
    def all_matches_stats(
        self: SyncPlayers[Model], player_id: t.Union[str, UUID], game: GameID
    ) -> ItemPage[BaseMatchPlayerStats]: ...

    def all_matches_stats(
        self, player_id: t.Union[str, UUID], game: GameID
    ) -> t.Union[ItemPage[BaseMatchPlayerStats], t.List[RawAPIItem]]:
        return self.__class__._sync_page_iterator.collect(
            self.matches_stats,  # type: ignore[misc]
            player_id,
            game,
            unix=self.__class__._unix_cfg(
                key="stats.Match Finished At", attr="match_finished_at"
            ),
        )

    @t.overload
    def history(
        self: SyncPlayers[Raw],
        player_id: t.Union[str, UUID],
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
        player_id: t.Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> ItemPage[Match]: ...

    @_validate_player_id
    @validate_call
    def history(
        self,
        player_id: t.Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> t.Union[RawAPIPageResponse, ItemPage[Match]]:
        return self._validate_response(
            self._client.get(
                self.path / str(player_id) / "history",
                params=self.__class__._build_params(
                    game=game, offset=offset, limit=limit, start=start, to=to
                ),
                expect_page=True,
            ),
            ItemPage[Match],
        )

    @t.overload
    def all_history(
        self: SyncPlayers[Raw], player_id: t.Union[str, UUID], game: GameID
    ) -> RawAPIPageResponse: ...

    @t.overload
    def all_history(
        self: SyncPlayers[Model], player_id: t.Union[str, UUID], game: GameID
    ) -> ItemPage[Match]: ...

    def all_history(
        self, player_id: t.Union[str, UUID], game: GameID
    ) -> t.Union[RawAPIPageResponse, ItemPage[Match]]:
        return self.__class__._sync_page_iterator.collect(
            self.history,  # type: ignore[misc]
            player_id,
            game,
            unix=self.__class__._unix_cfg(
                key="finished_at", attr="finished_at"
            ),
        )

    @t.overload
    def hubs(
        self: SyncPlayers[Raw],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def hubs(
        self: SyncPlayers[Model],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> ItemPage[Hub]: ...

    @_validate_player_id
    @validate_call
    def hubs(
        self,
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> t.Union[RawAPIPageResponse, ItemPage[Hub]]:
        return self._validate_response(
            self._client.get(
                self.path / str(player_id) / "hubs",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[Hub],
        )

    @_validate_player_id
    @validate_call
    def stats(self, player_id: t.Union[str, UUID], game: GameID) -> t.Any:
        # NOT IMPLEMENTED YET — Validator is not defined
        return self._validate_response(
            self._client.get(
                self.path / str(player_id) / "stats" / game, expect_page=True
            ),
            None,
        )

    @t.overload
    def teams(
        self: SyncPlayers[Raw],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def teams(
        self: SyncPlayers[Model],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[GeneralTeam]: ...

    @_validate_player_id
    @validate_call
    def teams(
        self,
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ItemPage[GeneralTeam]]:
        return self._validate_response(
            self._client.get(
                self.path / str(player_id) / "teams",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[GeneralTeam],
        )

    @t.overload
    def tournaments(
        self: SyncPlayers[Raw],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    def tournaments(
        self: SyncPlayers[Model],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[Tournament]: ...

    @_validate_player_id
    @validate_call
    def tournaments(
        self,
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ItemPage[Tournament]]:
        return self._validate_response(
            self._client.get(
                self.path / str(player_id) / "tournaments",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[Tournament],
        )


@t.final
class AsyncPlayers(BasePlayers[AsyncClient], t.Generic[APIResponseFormatT]):
    @t.overload
    async def get(
        self: AsyncPlayers[Raw], identifier: t.Union[str, UUID]
    ) -> RawAPIItem: ...

    @t.overload
    async def get(
        self: AsyncPlayers[Raw], *, game: GameID, game_player_id: str
    ) -> RawAPIItem: ...

    @t.overload
    async def get(
        self: AsyncPlayers[Model], identifier: t.Union[str, UUID]
    ) -> Player: ...

    @t.overload
    async def get(
        self: AsyncPlayers[Model], *, game: GameID, game_player_id: str
    ) -> Player: ...

    @validate_call
    async def get(
        self,
        identifier: t.Optional[t.Union[str, UUID]] = None,
        *,
        game: t.Optional[GameID] = None,
        game_player_id: t.Optional[str] = None,
    ) -> t.Union[RawAPIItem, Player]:
        """Fetch player data either by identifier or by game-specific parameters asynchronously.

        Args:
            identifier: Player's FACEIT UUID or nickname
            game: Game identifier (required if using game_player_id)
            game_player_id: Game-specific player ID (requires game parameter)

        Returns:
            Player model or raw dict depending on client configuration

        Examples:
            ```python
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
            ```
        """
        return self._validate_response(
            await self._client.get(
                **self._process_get_request(identifier, game, game_player_id),
                expect_item=True,
            ),
            Player,
        )

    __call__ = get

    @t.overload
    async def bans(
        self: AsyncPlayers[Raw],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def bans(
        self: AsyncPlayers[Model],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[BanEntry]: ...

    @_validate_player_id
    @validate_call
    async def bans(
        self,
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ItemPage[BanEntry]]:
        return self._validate_response(
            await self._client.get(
                self.path / str(player_id) / "bans",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[BanEntry],
        )

    @t.overload
    async def matches_stats(
        self: AsyncPlayers[Raw],
        player_id: t.Union[str, UUID],
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
        player_id: t.Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> ItemPage[CS2MatchPlayerStats]: ...

    @_validate_player_id
    @validate_call
    async def matches_stats(
        self,
        player_id: t.Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> t.Union[ItemPage[CS2MatchPlayerStats], RawAPIPageResponse]:
        return self._process_matches_stats_response(
            await self._client.get(
                self.path / str(player_id) / "games" / game / "stats",
                params=self.__class__._build_params(
                    offset=offset, limit=limit, start=start, to=to
                ),
                expect_page=True,
            ),
            game,
        )

    @t.overload
    async def history(
        self: AsyncPlayers[Raw],
        player_id: t.Union[str, UUID],
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
        player_id: t.Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> ItemPage[Match]: ...

    @_validate_player_id
    @validate_call
    async def history(
        self,
        player_id: t.Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: t.Optional[int] = None,
        to: t.Optional[int] = None,
    ) -> t.Union[RawAPIPageResponse, ItemPage[Match]]:
        return self._validate_response(
            await self._client.get(
                self.path / str(player_id) / "history",
                params=self.__class__._build_params(
                    game=game, offset=offset, limit=limit, start=start, to=to
                ),
                expect_page=True,
            ),
            ItemPage[Match],
        )

    @t.overload
    async def hubs(
        self: AsyncPlayers[Raw],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def hubs(
        self: AsyncPlayers[Model],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> ItemPage[Hub]: ...

    @_validate_player_id
    @validate_call
    async def hubs(
        self,
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> t.Union[RawAPIPageResponse, ItemPage[Hub]]:
        return self._validate_response(
            await self._client.get(
                self.path / str(player_id) / "hubs",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[Hub],
        )

    @_validate_player_id
    @validate_call
    async def stats(
        self, player_id: t.Union[str, UUID], game: GameID
    ) -> t.Any:
        # NOT IMPLEMENTED YET — Validator is not defined
        return self._validate_response(
            await self._client.get(
                self.path / str(player_id) / "stats" / game, expect_page=True
            ),
            None,
        )

    @t.overload
    async def teams(
        self: AsyncPlayers[Raw],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def teams(
        self: AsyncPlayers[Model],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[GeneralTeam]: ...

    @_validate_player_id
    @validate_call
    async def teams(
        self,
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ItemPage[GeneralTeam]]:
        return self._validate_response(
            await self._client.get(
                self.path / str(player_id) / "teams",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[GeneralTeam],
        )

    @t.overload
    async def tournaments(
        self: AsyncPlayers[Raw],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> RawAPIPageResponse: ...

    @t.overload
    async def tournaments(
        self: AsyncPlayers[Model],
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[Tournament]: ...

    @_validate_player_id
    @validate_call
    async def tournaments(
        self,
        player_id: t.Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> t.Union[RawAPIPageResponse, ItemPage[Tournament]]:
        return self._validate_response(
            await self._client.get(
                self.path / str(player_id) / "tournaments",
                params=self.__class__._build_params(
                    offset=offset, limit=limit
                ),
                expect_page=True,
            ),
            ItemPage[Tournament],
        )
