from __future__ import annotations

import typing

try:
    import decouple
except ModuleNotFoundError:
    decouple = None

import pytest

import faceit
from faceit.constants import GameID

if typing.TYPE_CHECKING:
    from faceit.api import AsyncDataResource, SyncDataResource

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        decouple is None or decouple.config("FACEIT_API_KEY", default=None) is None,
        reason="`decouple` not installed or `FACEIT_API_KEY` not found in environment or `.env` file",
    ),
]

DEFAULT_PLAYER: typing.Final = "zombyacoff"


@pytest.fixture(scope="module")
def test_player() -> str:
    return decouple.config("FACEIT_TEST_PLAYER", default=DEFAULT_PLAYER)


@pytest.fixture(scope="module")
def data() -> SyncDataResource:
    return faceit.SyncDataResource()


@pytest.fixture
async def async_data() -> typing.AsyncGenerator[AsyncDataResource, None]:
    async with faceit.AsyncDataResource() as client:
        yield client


def test_sync_player_flow(data: SyncDataResource, test_player: str) -> None:
    player = data.players.get(test_player)

    assert player.nickname == test_player
    assert player.id is not None

    matches = data.raw_players.matches_stats(player.id, GameID.CS2, limit=2)

    assert isinstance(matches, dict)
    if "items" in matches:
        assert len(matches["items"]) > 0
        assert "match_id" in matches["items"][0] or "stats" in matches["items"][0]


def test_sync_games_list(data: SyncDataResource) -> None:
    games_page = data.raw_games.items(limit=10)

    assert "items" in games_page
    assert len(games_page["items"]) > 0

    game_ids = [g["game_id"] for g in games_page["items"]]
    assert "cs2" in game_ids or "csgo" in game_ids


async def test_async_player_flow(
    async_data: AsyncDataResource, test_player: str
) -> None:
    player = await async_data.players.get(test_player)

    assert player.nickname == test_player
    assert player.id is not None


def test_pagination_loop_e2e(data: SyncDataResource) -> None:
    games = data.raw_games.all_items(max_items=3)
    assert len(games) >= 3
