from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch

import pytest

from faceit.api import AsyncDataResource, SyncDataResource

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator


@pytest.fixture
def mock_sync_data(valid_uuid: str) -> Generator[SyncDataResource, None, None]:
    with patch("httpx.Client") as mock_httpx:
        mock_instance = mock_httpx.return_value
        mock_instance.is_closed = False

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "mocked"}
        mock_instance.request.return_value = mock_response

        yield SyncDataResource(valid_uuid)


@pytest.fixture
def mock_async_data(valid_uuid: str) -> AsyncGenerator[AsyncDataResource, None]:
    async def _mock_async() -> AsyncGenerator[AsyncDataResource, None]:  # noqa: RUF029
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_instance = mock_httpx.return_value
            mock_instance.is_closed = False
            mock_instance.aclose = AsyncMock()

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": "mocked"}
            mock_instance.request = AsyncMock(return_value=mock_response)

            yield AsyncDataResource(valid_uuid)

    return _mock_async()


def test_games_items(mock_sync_data: SyncDataResource) -> None:
    mock_sync_data.raw_games.items(offset=10, limit=50)

    mock_client = mock_sync_data.client._client
    args, kwargs = mock_client.request.call_args
    assert str(args[1]).endswith("/games")
    assert kwargs["params"] == {"offset": 10, "limit": 50}


def test_matches_get_and_stats(
    mock_sync_data: SyncDataResource, valid_uuid: str
) -> None:
    match_id = f"1-{valid_uuid}"

    mock_sync_data.raw_matches.get(match_id)
    args, _ = mock_sync_data.client._client.request.call_args
    assert str(args[1]).endswith(f"/matches/{match_id}")

    mock_sync_data.raw_matches.stats(match_id)
    args, _ = mock_sync_data.client._client.request.call_args
    assert str(args[1]).endswith(f"/matches/{match_id}/stats")


def test_championships_get(mock_sync_data: SyncDataResource, valid_uuid: str) -> None:
    champ_id = valid_uuid
    mock_sync_data.raw_championships.get(champ_id)
    args, _ = mock_sync_data.client._client.request.call_args
    assert str(args[1]).endswith(f"/championships/{champ_id}")


def test_teams_get(mock_sync_data: SyncDataResource, valid_uuid: str) -> None:
    team_id = f"team-{valid_uuid}"
    mock_sync_data.raw_teams.get(team_id)
    args, _ = mock_sync_data.client._client.request.call_args
    assert str(args[1]).endswith(f"/teams/{team_id}")


async def test_async_games_items(
    mock_async_data: AsyncGenerator[AsyncDataResource, None],
) -> None:
    async for data in mock_async_data:
        await data.raw_games.items(offset=5)
        mock_client = data.client._client
        args, kwargs = mock_client.request.call_args
        assert str(args[1]).endswith("/games")
        assert kwargs["params"]["offset"] == 5
        await data.client.aclose()
