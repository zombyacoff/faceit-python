from __future__ import annotations

import typing
from unittest.mock import AsyncMock, Mock, patch

import pytest

from faceit.constants import GameID

if typing.TYPE_CHECKING:
    from faceit.api.data.players import AsyncPlayers, SyncPlayers


def test_process_get_request_requires_game_and_game_player_id(
    sync_players_raw: SyncPlayers[typing.Any],
) -> None:
    with pytest.raises(ValueError):
        sync_players_raw._process_get_request(None, None, None)


def test_process_get_request_by_nickname(
    sync_players_raw: SyncPlayers[typing.Any],
) -> None:
    payload = sync_players_raw._process_get_request("zomby", None, None)

    assert str(payload["endpoint"]) == "players"
    assert payload["params"] == {"nickname": "zomby"}


def test_process_get_request_by_uuid(
    sync_players_raw: SyncPlayers[typing.Any], valid_uuid: str
) -> None:
    payload = sync_players_raw._process_get_request(valid_uuid, None, None)
    assert str(payload["endpoint"]) == f"players/{valid_uuid}"
    assert payload["params"] == {}


def test_process_get_request_warns_when_lookup_key_conflicts_with_game_filters(
    sync_players_raw: SyncPlayers[typing.Any],
) -> None:
    with pytest.warns(UserWarning):
        payload = sync_players_raw._process_get_request(
            "nickname",
            GameID.CS2,
            "steam-123",
        )
    assert payload["params"]["nickname"] == "nickname"


def test_sync_get_calls_client_with_expect_item(
    sync_players_raw: SyncPlayers[typing.Any], mock_sync_client: Mock
) -> None:
    result = sync_players_raw.get("nickname")

    assert result == {"player_id": "p1"}
    mock_sync_client.get.assert_called_once()
    kwargs = mock_sync_client.get.call_args.kwargs
    assert kwargs["expect_item"] is True
    assert str(kwargs["endpoint"]) == "players"
    assert kwargs["params"] == {"nickname": "nickname"}


def test_sync_all_matches_stats_delegates_to_pagination_with_unix_cfg(
    sync_players_raw: SyncPlayers[typing.Any], valid_uuid: str
) -> None:
    with patch.object(
        sync_players_raw.__class__._sync_page_iterator,
        "gather_pages",
        return_value=[{"id": "m1"}],
    ) as gather_pages:
        result = sync_players_raw.all_matches_stats(valid_uuid, GameID.CS2)

    assert result == [{"id": "m1"}]
    gather_pages.assert_called_once()
    _, args, kwargs = gather_pages.mock_calls[0]
    assert args[0] == sync_players_raw.matches_stats
    assert args[1] == valid_uuid
    assert args[2] == GameID.CS2
    assert kwargs["unix"] == sync_players_raw.__class__._matches_stats_timestamp_cfg


@pytest.mark.asyncio
async def test_async_get_calls_client_with_expect_item(
    async_players_raw: AsyncPlayers[typing.Any], mock_async_client: Mock
) -> None:
    result = await async_players_raw.get("nickname")

    assert result == {"player_id": "p1"}
    mock_async_client.get.assert_awaited_once()
    kwargs = mock_async_client.get.call_args.kwargs
    assert kwargs["expect_item"] is True
    assert str(kwargs["endpoint"]) == "players"
    assert kwargs["params"] == {"nickname": "nickname"}


@pytest.mark.asyncio
async def test_async_all_history_delegates_to_pagination_with_unix_cfg(
    async_players_raw: AsyncPlayers[typing.Any], valid_uuid: str
) -> None:
    with patch.object(
        async_players_raw.__class__._async_page_iterator,
        "gather_pages",
        new=AsyncMock(return_value=[{"id": "h1"}]),
    ) as gather_pages:
        result = await async_players_raw.all_history(valid_uuid, GameID.CS2)

    assert result == [{"id": "h1"}]
    gather_pages.assert_awaited_once()
    _, args, kwargs = gather_pages.mock_calls[0]
    assert args[0] == async_players_raw.history
    assert args[1] == valid_uuid
    assert args[2] == GameID.CS2
    assert kwargs["unix"] == async_players_raw.__class__._history_timestamp_cfg
