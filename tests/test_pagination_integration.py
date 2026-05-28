from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from faceit.api import AsyncDataResource, SyncDataResource


@pytest.fixture
def mock_api_key(valid_uuid: str) -> str:
    return valid_uuid


def test_sync_pagination_all_items(mock_api_key: str) -> None:
    with patch("httpx.Client") as mock_httpx:
        mock_instance = mock_httpx.return_value
        mock_instance.is_closed = False

        page1 = {
            "items": [{"id": str(i)} for i in range(100)],
            "offset": 0,
            "limit": 100,
        }
        page2 = {"items": [{"id": "100"}], "offset": 100, "limit": 100}

        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = page1

        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = page2

        mock_instance.request.side_effect = [mock_response1, mock_response2]

        data = SyncDataResource(mock_api_key)
        results = data.raw_games.all_items(max_items=101)

        assert len(results) == 101
        assert results[0]["id"] == "0"
        assert results[100]["id"] == "100"
        assert mock_instance.request.call_count == 2


async def test_async_pagination_all_items(mock_api_key: str) -> None:
    with patch("httpx.AsyncClient") as mock_httpx:
        mock_instance = mock_httpx.return_value
        mock_instance.is_closed = False
        mock_instance.aclose = AsyncMock()

        page1 = {
            "items": [{"id": str(i)} for i in range(100)],
            "offset": 0,
            "limit": 100,
        }
        page2 = {"items": [{"id": "100"}], "offset": 100, "limit": 100}

        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = page1

        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = page2

        mock_instance.request = AsyncMock(side_effect=[mock_response1, mock_response2])

        data = AsyncDataResource(mock_api_key)
        results = await data.raw_games.all_items(max_items=101)

        assert len(results) == 101
        assert mock_instance.request.call_count == 2
        await data.client.aclose()
