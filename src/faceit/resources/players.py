from __future__ import annotations

import logging
import warnings
from abc import ABC
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union, final, overload
from uuid import UUID

from pydantic import Field, validate_call

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
from faceit.types import ClientT, Model, ParamSpec, Raw, ResponseFormat, TypeAlias
from faceit.utils import convert_to_unix_millis, is_valid_uuid, validate_uuid_args  # noqa: F401 TODO

from .base import BaseResource, FaceitResourcePath

# Import `_RawResponsePage` to avoid duplication of complex type in `_process_matches_stats_response`
from .pagination import _RawResponsePage, acollect, collect  # noqa: F401 TODO

_logger = logging.getLogger(__name__)

_T = TypeVar("_T")
_P = ParamSpec("_P")


def _validate_player_id(func: Callable[_P, _T]) -> Callable[_P, _T]:
    """Alias for `validate_uuid_args("player_id")`."""
    return validate_uuid_args("player_id")(func)


# The returned types in the `matches_stats` method mirror what could be returned
# in the Model version. This alias eliminates duplication between `overload` signatures
# and implementation, making future type changes easier to maintain
_MatchesStatsResponse: TypeAlias = Union[ItemPage[CS2MatchPlayerStats], Dict[str, Any]]
_AllMatchesStatsResponse: TypeAlias = Optional[Union[ItemPage[BaseMatchPlayerStats], List[Dict[str, Any]]]]


class BasePlayers(BaseResource[ClientT], ABC):
    _resource_path = FaceitResourcePath.PLAYERS
    _match_stats_model_types: Dict[GameID, Type[BaseMatchPlayerStats]] = {
        GameID.CS2: CS2MatchPlayerStats,
        # TODO GameID.CSGO: CSGOMatchPlayerStats,
    }

    def _process_get_request(
        self, identifier: Optional[Union[str, UUID]], game: Optional[GameID], game_player_id: Optional[str]
    ) -> Dict[str, Any]:
        """Build and return the request payload (`endpoint` and `params`) for the `get` method."""
        params = self.__class__._build_params(game=game, game_player_id=game_player_id)

        if identifier is None:
            if game is None or game_player_id is None:
                raise ValueError(
                    "When 'identifier' is not provided, both 'game' AND 'game_player_id' must be specified"
                )
            _logger.info("Fetching player by game parameters: game=%s, game_player_id=%s", game, game_player_id)
            return self.__class__._build_request_payload(self.path, params)

        if game is not None or game_player_id is not None:
            warnings.warn(
                "When 'identifier' is provided, 'game' and 'game_player_id' should not be specified",
                UserWarning,
                stacklevel=3,
            )

        if is_valid_uuid(identifier):
            _logger.info("Fetching player by UUID: %s", identifier)
            return self.__class__._build_request_payload(self.path / str(identifier), params)

        _logger.info("Fetching player by nickname: %s", identifier)
        params.update(nickname=str(identifier))
        return self.__class__._build_request_payload(self.path, params)

    # TODO: Выделить данную логику в универсальный метод класса,
    # так как весьма вероятно, что она будет использоваться в других ресурсах
    def _process_matches_stats_response(self, response: Dict[str, Any], game: GameID) -> _RawResponsePage:
        """Process the response from the matches stats endpoint."""
        _logger.debug("Processing match stats response for game: %s", game)

        validator = self._match_stats_model_types.get(game)
        if validator is not None:
            _logger.info("Validating match stats with model for game: %s", game)
            # Suppressing type checking warning because we're using a dynamic runtime subscript.
            # `ItemPage` is being subscripted with a variable (`validator`) which mypy cannot statically verify.
            return self._validate_response(response, ItemPage[validator])  # type: ignore[valid-type]

        warnings.warn(f"No model defined for game '{game}'. Consider using the raw response", UserWarning, stacklevel=3)
        return response


@final
class SyncPlayers(BasePlayers[SyncClient], Generic[ResponseFormat]):
    @overload
    def get(self: SyncPlayers[Raw], identifier: Union[str, UUID]) -> Dict[str, Any]: ...
    @overload
    def get(self: SyncPlayers[Raw], *, game: GameID, game_player_id: str) -> Dict[str, Any]: ...
    @overload
    def get(self: SyncPlayers[Model], identifier: Union[str, UUID]) -> Player: ...
    @overload
    def get(self: SyncPlayers[Model], *, game: GameID, game_player_id: str) -> Player: ...
    def get(
        self,
        identifier: Optional[Union[str, UUID]] = None,
        *,
        game: Optional[GameID] = None,
        game_player_id: Optional[str] = None,
    ) -> Union[Player, Dict[str, Any]]:
        """Fetch player data either by identifier or by game-specific parameters.

        Args:
            identifier: Player's FACEIT UUID or nickname
            game: Game identifier (required if using game_player_id)
            game_player_id: Game-specific player ID (requires game parameter)

        Returns:
            Player model or raw dict depending on client configuration

        Examples:
            ```
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
        # fmt: off
        return self._validate_response(self._client.get(
            **self._process_get_request(identifier, game, game_player_id)), Player
        )
        # fmt: on

    # This creates an alias allowing instances to be called directly like `resource(...)`
    # instead of `resource.get(...)`. While both forms are valid, using the explicit `.get()`
    # method is generally preferred for clarity. NOTE: The alias is maintained for convenience
    __call__ = get

    @overload
    def bans(
        self: SyncPlayers[Raw],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> Dict[str, Any]: ...
    @overload
    def bans(
        self: SyncPlayers[Model],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[BanEntry]: ...
    @_validate_player_id
    @validate_call
    def bans(
        self,
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> Union[ItemPage[BanEntry], Dict[str, Any]]:
        # fmt: off
        return self._validate_response(self._client.get(
            self.path / str(player_id) / "bans",
            params=self.__class__._build_params(offset=offset, limit=limit)),
            ItemPage[BanEntry],
        )
        # fmt: on

    @overload
    def all_bans(self: SyncPlayers[Raw], player_id: Union[str, UUID]) -> Optional[List[Dict[str, Any]]]: ...
    @overload
    def all_bans(self: SyncPlayers[Model], player_id: Union[str, UUID]) -> Optional[ItemPage[BanEntry]]: ...
    def all_bans(self, player_id: Union[str, UUID]) -> Optional[Union[ItemPage[BanEntry], List[Dict[str, Any]]]]:
        # Ignore mypy error: `collect()` infers return type based on the method's signature,
        # but mypy can't properly track generic type parameters through this pattern
        return collect(self.bans, player_id)  # type: ignore[misc]

    @overload
    def matches_stats(
        self: SyncPlayers[Raw],
        player_id: Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: Optional[int] = None,
        to: Optional[int] = None,
    ) -> Dict[str, Any]: ...
    # NOTE: Currently, there is only one model for validating game statistics - so we return only it.
    # In the future, when expanding the models, we will need to devise a solution for the return value
    @overload
    def matches_stats(
        self: SyncPlayers[Model],
        player_id: Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: Optional[int] = None,
        to: Optional[int] = None,
    ) -> _MatchesStatsResponse: ...
    @_validate_player_id
    @validate_call
    def matches_stats(
        self,
        player_id: Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: Optional[int] = None,
        to: Optional[int] = None,
    ) -> _MatchesStatsResponse:
        # fmt: off
        return self._process_matches_stats_response(self._client.get(
            self.path / str(player_id) / "games" / game / "stats",
            params=self.__class__._build_params(
                offset=offset, limit=limit, start=start, to=to
            )), game,  # `game` parameter is used to select the appropriate model for validation
        )
        # fmt: on

    @overload
    def all_matches_stats(
        self: SyncPlayers[Raw], player_id: Union[str, UUID], game: GameID
    ) -> Optional[List[Dict[str, Any]]]: ...
    @overload
    def all_matches_stats(
        self: SyncPlayers[Model], player_id: Union[str, UUID], game: GameID
    ) -> _AllMatchesStatsResponse: ...
    def all_matches_stats(self, player_id: Union[str, UUID], game: GameID) -> _AllMatchesStatsResponse:
        # fmt: off
        return collect(
            self.matches_stats, player_id, game,  # type: ignore[misc]
            deduplicate=True, use_unix_pagination=True,
            dict_unix_key="stats.Match Finished At", model_unix_attr="match_finished_at",
        )
        # fmt: on

    @overload
    def history(
        self: SyncPlayers[Raw],
        player_id: Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: Optional[int] = None,
        to: Optional[int] = None,
    ) -> Dict[str, Any]: ...
    @overload
    def history(
        self: SyncPlayers[Model],
        player_id: Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: Optional[int] = None,
        to: Optional[int] = None,
    ) -> ItemPage[Match]: ...
    @_validate_player_id
    @validate_call
    def history(
        self,
        player_id: Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: Optional[int] = None,
        to: Optional[int] = None,
    ) -> Union[ItemPage[Match], Dict[str, Any]]:
        # fmt: off
        return self._validate_response(self._client.get(
            self.path / str(player_id) / "history",
            params=self.__class__._build_params(
                game=game, offset=offset, limit=limit, start=start, to=to
            )),
            ItemPage[Match],
        )
        # fmt: on

    @overload
    def all_history(
        self: SyncPlayers[Raw], player_id: Union[str, UUID], game: GameID
    ) -> Optional[List[Dict[str, Any]]]: ...
    @overload
    def all_history(
        self: SyncPlayers[Model], player_id: Union[str, UUID], game: GameID
    ) -> Optional[ItemPage[Match]]: ...
    def all_history(
        self, player_id: Union[str, UUID], game: GameID
    ) -> Optional[Union[ItemPage[Match], Optional[List[Dict[str, Any]]]]]:
        timestamp_field_name = "finished_at"
        # fmt: off
        return collect(
            self.history, player_id, game,  # type: ignore[misc]
            deduplicate=True, use_unix_pagination=True,
            dict_unix_key=timestamp_field_name, model_unix_attr=timestamp_field_name
        )
        # fmt: on

    @overload
    def hubs(
        self: SyncPlayers[Raw],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> Dict[str, Any]: ...
    @overload
    def hubs(
        self: SyncPlayers[Model],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> ItemPage[Hub]: ...
    @_validate_player_id
    @validate_call
    def hubs(
        self,
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> Union[ItemPage[Hub], Dict[str, Any]]:
        # fmt: off
        return self._validate_response(self._client.get(
            self.path / str(player_id) / "hubs",
            params=self.__class__._build_params(offset=offset, limit=limit)),
            ItemPage[Hub],
        )
        # fmt: on

    @overload
    def all_hubs(self: SyncPlayers[Raw], player_id: Union[str, UUID]) -> Optional[List[Dict[str, Any]]]: ...
    @overload
    def all_hubs(self: SyncPlayers[Model], player_id: Union[str, UUID]) -> Optional[ItemPage[Hub]]: ...
    def all_hubs(self, player_id: Union[str, UUID]) -> Optional[Union[ItemPage[Hub], List[Dict[str, Any]]]]:
        return collect(self.hubs, player_id)  # type: ignore[misc]

    @_validate_player_id
    @validate_call
    def stats(self, player_id: Union[str, UUID], game: GameID) -> Union[Any, Dict[str, Any]]:
        # NOT IMPLEMENTED YET — Validator is not defined
        # fmt: off
        return self._validate_response(self._client.get(
            self.path / str(player_id) / "stats" / game),
            None,
        )
        # fmt: on

    @overload
    def teams(
        self: SyncPlayers[Raw],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> Dict[str, Any]: ...
    @overload
    def teams(
        self: SyncPlayers[Model],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[GeneralTeam]: ...
    @_validate_player_id
    @validate_call
    def teams(
        self,
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> Union[ItemPage[GeneralTeam], Dict[str, Any]]:
        # fmt: off
        return self._validate_response(self._client.get(
            self.path / str(player_id) / "teams",
            params=self.__class__._build_params(offset=offset, limit=limit)),
            ItemPage[GeneralTeam],
        )
        # fmt: on

    @overload
    def tournaments(
        self: SyncPlayers[Raw],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> Dict[str, Any]: ...
    @overload
    def tournaments(
        self: SyncPlayers[Model],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[Tournament]: ...
    @_validate_player_id
    @validate_call
    def tournaments(
        self,
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> Union[ItemPage[Tournament], Dict[str, Any]]:
        # fmt: off
        return self._validate_response(self._client.get(
            self.path / str(player_id) / "tournaments",
            params=self.__class__._build_params(
                offset=offset, limit=limit
            )),
            ItemPage[Tournament],
        )
        # fmt: on


@final
class AsyncPlayers(BasePlayers[AsyncClient], Generic[ResponseFormat]):
    @overload
    async def get(self: AsyncPlayers[Raw], identifier: Union[str, UUID]) -> Dict[str, Any]: ...
    @overload
    async def get(self: AsyncPlayers[Raw], *, game: GameID, game_player_id: str) -> Dict[str, Any]: ...
    @overload
    async def get(self: AsyncPlayers[Model], identifier: Union[str, UUID]) -> Player: ...
    @overload
    async def get(self: AsyncPlayers[Model], *, game: GameID, game_player_id: str) -> Player: ...
    @validate_call
    async def get(
        self,
        identifier: Optional[Union[str, UUID]] = None,
        *,
        game: Optional[GameID] = None,
        game_player_id: Optional[str] = None,
    ) -> Union[Player, Dict[str, Any]]:
        """Fetch player data either by identifier or by game-specific parameters asynchronously.

        Args:
            identifier: Player's FACEIT UUID or nickname
            game: Game identifier (required if using game_player_id)
            game_player_id: Game-specific player ID (requires game parameter)

        Returns:
            Player model or raw dict depending on client configuration

        Examples:
            ```
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
        # fmt: off
        return self._validate_response(await self._client.get(
            **self._process_get_request(identifier, game, game_player_id)), Player
        )
        # fmt: on

    # See the explanation of the existence of this
    # alias in the synchronous implementation of the class
    __call__ = get

    @overload
    async def bans(
        self: AsyncPlayers[Raw],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> Dict[str, Any]: ...
    @overload
    async def bans(
        self: AsyncPlayers[Model],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[BanEntry]: ...
    @_validate_player_id
    @validate_call
    async def bans(
        self,
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> Union[ItemPage[BanEntry], Dict[str, Any]]:
        # fmt: off
        return self._validate_response(await self._client.get(
            self.path / str(player_id) / "bans",
            params=self.__class__._build_params(offset=offset, limit=limit)),
            ItemPage[BanEntry],
        )
        # fmt: on

    @overload
    async def matches_stats(
        self: AsyncPlayers[Raw],
        player_id: Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: Optional[int] = None,
        to: Optional[int] = None,
    ) -> Dict[str, Any]: ...
    @overload
    async def matches_stats(
        self: AsyncPlayers[Model],
        player_id: Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: Optional[int] = None,
        to: Optional[int] = None,
    ) -> _MatchesStatsResponse: ...
    @_validate_player_id
    @validate_call
    async def matches_stats(
        self,
        player_id: Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=200),
        limit: int = Field(20, ge=1, le=100),
        start: Optional[int] = None,
        to: Optional[int] = None,
    ) -> _MatchesStatsResponse:
        # fmt: off
        return self._process_matches_stats_response(await self._client.get(
            self.path / str(player_id) / "games" / game / "stats",
            params=self.__class__._build_params(
                offset=offset, limit=limit, start=start, to=to
            )), game,
        )
        # fmt: on

    @overload
    async def history(
        self: AsyncPlayers[Raw],
        player_id: Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: Optional[int] = None,
        to: Optional[int] = None,
    ) -> Dict[str, Any]: ...
    @overload
    async def history(
        self: AsyncPlayers[Model],
        player_id: Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: Optional[int] = None,
        to: Optional[int] = None,
    ) -> ItemPage[Match]: ...
    @_validate_player_id
    @validate_call
    async def history(
        self,
        player_id: Union[str, UUID],
        game: GameID,
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(20, ge=1, le=100),
        start: Optional[int] = None,
        to: Optional[int] = None,
    ) -> Union[ItemPage[Match], Dict[str, Any]]:
        # fmt: off
        return self._validate_response(await self._client.get(
            self.path / str(player_id) / "history",
            params=self.__class__._build_params(
                game=game, offset=offset, limit=limit, start=start, to=to
            )),
            ItemPage[Match],
        )
        # fmt: on

    @overload
    async def hubs(
        self: AsyncPlayers[Raw],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> Dict[str, Any]: ...
    @overload
    async def hubs(
        self: AsyncPlayers[Model],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> ItemPage[Hub]: ...
    @_validate_player_id
    @validate_call
    async def hubs(
        self,
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0, le=1000),
        limit: int = Field(50, ge=1, le=50),
    ) -> Union[ItemPage[Hub], Dict[str, Any]]:
        # fmt: off
        return self._validate_response(await self._client.get(
            self.path / str(player_id) / "hubs",
            params=self.__class__._build_params(offset=offset, limit=limit)),
            ItemPage[Hub],
        )
        # fmt: on

    @_validate_player_id
    @validate_call
    async def stats(self, player_id: Union[str, UUID], game: GameID) -> Union[Any, Dict[str, Any]]:
        # NOT IMPLEMENTED YET — Validator is not defined
        # fmt: off
        return self._validate_response(await self._client.get(
            self.path / str(player_id) / "stats" / game),
            None,
        )
        # fmt: on

    @overload
    async def teams(
        self: AsyncPlayers[Raw],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> Dict[str, Any]: ...
    @overload
    async def teams(
        self: AsyncPlayers[Model],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[GeneralTeam]: ...
    @_validate_player_id
    @validate_call
    async def teams(
        self,
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> Union[ItemPage[GeneralTeam], Dict[str, Any]]:
        # fmt: off
        return self._validate_response(await self._client.get(
            self.path / str(player_id) / "teams",
            params=self.__class__._build_params(offset=offset, limit=limit)),
            ItemPage[GeneralTeam],
        )
        # fmt: on

    @overload
    async def tournaments(
        self: AsyncPlayers[Raw],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> Dict[str, Any]: ...
    @overload
    async def tournaments(
        self: AsyncPlayers[Model],
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> ItemPage[Tournament]: ...
    @_validate_player_id
    @validate_call
    async def tournaments(
        self,
        player_id: Union[str, UUID],
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(20, ge=1, le=100),
    ) -> Union[ItemPage[Tournament], Dict[str, Any]]:
        # fmt: off
        return self._validate_response(await self._client.get(
            self.path / str(player_id) / "tournaments",
            params=self.__class__._build_params(
                offset=offset, limit=limit
            )),
            ItemPage[Tournament],
        )
        # fmt: on
