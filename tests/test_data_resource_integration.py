from unittest.mock import AsyncMock, Mock, patch

import pytest

from faceit.api import AsyncDataResource, SyncDataResource
from faceit.api.data.games import AsyncGames, SyncGames
from faceit.api.data.players import AsyncPlayers, SyncPlayers
from faceit.http import AsyncClient, SyncClient


@pytest.fixture
def mock_api_key(valid_uuid: str) -> str:
    return valid_uuid


def test_sync_data_resource_init(mock_api_key: str) -> None:
    with patch("httpx.Client"):
        data = SyncDataResource(mock_api_key)
        assert isinstance(data.client, SyncClient)
        assert data.client._api_key == mock_api_key


async def test_async_data_resource_init(mock_api_key: str) -> None:
    with patch("httpx.AsyncClient"):
        data = AsyncDataResource(mock_api_key)
        assert isinstance(data.client, AsyncClient)
        assert data.client._api_key == mock_api_key
        await data.client.aclose()


def test_sync_resources_accessibility(mock_api_key: str) -> None:
    with patch("httpx.Client"):
        data = SyncDataResource(mock_api_key)

        assert isinstance(data.players, SyncPlayers)
        assert isinstance(data.raw_players, SyncPlayers)
        assert isinstance(data.games, SyncGames)
        assert isinstance(data.raw_games, SyncGames)

        assert data.players.is_raw is False
        assert data.raw_players.is_raw is True


async def test_async_resources_accessibility(mock_api_key: str) -> None:
    with patch("httpx.AsyncClient"):
        data = AsyncDataResource(mock_api_key)

        assert isinstance(data.players, AsyncPlayers)
        assert isinstance(data.raw_players, AsyncPlayers)
        assert isinstance(data.games, AsyncGames)

        assert data.players.is_raw is False
        assert data.raw_players.is_raw is True
        await data.client.aclose()


def test_sync_request_flow(mock_api_key: str) -> None:
    with patch("httpx.Client") as mock_httpx:
        mock_instance = mock_httpx.return_value
        mock_instance.is_closed = False

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "player_id": "test-id",
            "nickname": "test-user",
        }
        mock_instance.request.return_value = mock_response

        data = SyncDataResource(mock_api_key)
        player_raw = data.raw_players.get("test-user")

        assert player_raw["nickname"] == "test-user"
        mock_instance.request.assert_called_once()
        args, kwargs = mock_instance.request.call_args
        assert args[0] == "GET"
        assert "players" in str(args[1])
        assert kwargs["params"] == {"nickname": "test-user"}


async def test_async_request_flow(mock_api_key: str) -> None:
    with patch("httpx.AsyncClient") as mock_httpx:
        mock_instance = mock_httpx.return_value
        mock_instance.is_closed = False
        mock_instance.aclose = AsyncMock()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "player_id": "test-id",
            "nickname": "test-user",
        }
        mock_instance.request = AsyncMock(return_value=mock_response)

        data = AsyncDataResource(mock_api_key)
        player_raw = await data.raw_players.get("test-user")

        assert player_raw["nickname"] == "test-user"
        mock_instance.request.assert_called_once()
        await data.client.aclose()


def test_context_manager_sync(mock_api_key: str) -> None:
    with patch("httpx.Client") as mock_httpx:
        mock_instance = mock_httpx.return_value
        mock_instance.is_closed = False

        with SyncDataResource(mock_api_key) as data:
            assert isinstance(data, SyncDataResource)

        mock_instance.close.assert_called_once()


async def test_context_manager_async(mock_api_key: str) -> None:
    with patch("httpx.AsyncClient") as mock_httpx:
        mock_instance = mock_httpx.return_value
        mock_instance.is_closed = False
        mock_instance.aclose = AsyncMock()

        async with AsyncDataResource(mock_api_key) as data:
            assert isinstance(data, AsyncDataResource)

        mock_instance.aclose.assert_called_once()
