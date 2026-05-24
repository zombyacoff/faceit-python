from typing import Any
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from faceit.api.data.players import AsyncPlayers, SyncPlayers


@pytest.fixture
def valid_uuid() -> str:
    return str(uuid4())


@pytest.fixture(scope="module")
def mock_sync_client() -> Mock:
    client = Mock()
    client.get.return_value = {"player_id": "p1"}
    return client


@pytest.fixture(scope="module")
def mock_async_client() -> Mock:
    client = Mock()
    client.get = AsyncMock(return_value={"player_id": "p1"})
    return client


@pytest.fixture(scope="module")
def sync_players_raw(mock_sync_client: Mock) -> SyncPlayers[Any]:
    return SyncPlayers(mock_sync_client, raw=True)


@pytest.fixture(scope="module")
def async_players_raw(mock_async_client: Mock) -> AsyncPlayers[Any]:
    return AsyncPlayers(mock_async_client, raw=True)
