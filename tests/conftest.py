import typing
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from faceit.api.data.players import AsyncPlayers, SyncPlayers


@pytest.fixture
def valid_uuid() -> str:
    return str(uuid4())


@pytest.fixture
def mock_sync_client() -> Mock:
    client = Mock()
    client.get.return_value = {"player_id": "p1"}
    return client


@pytest.fixture
def mock_async_client() -> Mock:
    client = Mock()
    client.get = AsyncMock(return_value={"player_id": "p1"})
    return client


@pytest.fixture
def sync_players_raw(mock_sync_client: Mock) -> SyncPlayers[typing.Any]:
    return SyncPlayers(client=mock_sync_client, raw=True)


@pytest.fixture
def async_players_raw(mock_async_client: Mock) -> AsyncPlayers[typing.Any]:
    return AsyncPlayers(client=mock_async_client, raw=True)
