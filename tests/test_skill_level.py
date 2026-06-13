from __future__ import annotations

import pytest
from pydantic import ValidationError

from faceit import GameID, SkillLevel


@pytest.fixture
def cs2_lvl1() -> SkillLevel:
    return SkillLevel.get_level(GameID.CS2, 1)


@pytest.fixture
def cs2_lvl2() -> SkillLevel:
    return SkillLevel.get_level(GameID.CS2, 2)


@pytest.fixture
def cs2_lvl10() -> SkillLevel:
    return SkillLevel.get_level(GameID.CS2, 10)


@pytest.fixture
def csgo_lvl1() -> SkillLevel:
    return SkillLevel.get_level(GameID.CSGO, 1)


def test_get_level_by_level() -> None:
    lvl = SkillLevel.get_level(GameID.CS2, 5)
    assert lvl is not None
    assert lvl.level == 5
    assert lvl.game_id == GameID.CS2


def test_get_level_by_elo() -> None:
    lvl = SkillLevel.get_level(GameID.CS2, elo=300)
    assert lvl is not None
    assert lvl.level == 1
    lvl10 = SkillLevel.get_level(GameID.CS2, elo=2500)
    assert lvl10 is not None
    assert lvl10.level == 10


def test_get_level_invalid_game() -> None:
    with pytest.raises(ValidationError):
        SkillLevel.get_level("NOT_IN_GAMEID", 1)

    with pytest.warns(UserWarning, match="Game .* is not supported"):
        assert SkillLevel.get_level(GameID.FIFA23, 1) is None


def test_get_level_no_params_raises_error() -> None:
    with pytest.raises(ValueError, match="Either level or elo must be specified"):
        SkillLevel.get_level(GameID.CS2)


def test_get_all_levels() -> None:
    levels = SkillLevel.get_all_levels(GameID.CS2)
    assert len(levels) == 10
    assert all(isinstance(L, SkillLevel) for L in levels)
    assert [L.level for L in levels] == list(range(1, 11))


def test_is_highest_level(cs2_lvl1: SkillLevel, cs2_lvl10: SkillLevel) -> None:
    assert not cs2_lvl1.is_highest_level
    assert cs2_lvl10.is_highest_level


def test_range_size(cs2_lvl1: SkillLevel, cs2_lvl10: SkillLevel) -> None:
    assert cs2_lvl1.range_size == 401
    assert cs2_lvl10.range_size is None


def test_next_previous_level(
    cs2_lvl1: SkillLevel, cs2_lvl2: SkillLevel, cs2_lvl10: SkillLevel
) -> None:
    assert cs2_lvl1.next_level == cs2_lvl2
    assert cs2_lvl2.previous_level == cs2_lvl1
    assert cs2_lvl1.previous_level is None
    assert cs2_lvl10.next_level is None


def test_elo_needed_for_next_level(cs2_lvl1: SkillLevel, cs2_lvl10: SkillLevel) -> None:
    assert cs2_lvl1.elo_needed_for_next_level == 401
    assert cs2_lvl10.elo_needed_for_next_level is None


def test_contains_elo(cs2_lvl1: SkillLevel) -> None:
    assert cs2_lvl1.contains_elo(100)
    assert cs2_lvl1.contains_elo(500)
    assert not cs2_lvl1.contains_elo(501)
    assert not cs2_lvl1.contains_elo(-1)


def test_progress_percentage(cs2_lvl1: SkillLevel) -> None:
    import math  # noqa: PLC0415

    assert math.isclose(cs2_lvl1.progress_percentage(250), 37.5)
    assert math.isclose(cs2_lvl1.progress_percentage(100), 0.0)
    assert math.isclose(cs2_lvl1.progress_percentage(500), 100.0)


def test_progress_percentage_warnings(
    cs2_lvl1: SkillLevel, cs2_lvl10: SkillLevel
) -> None:
    with pytest.warns(UserWarning, match="Cannot calculate progress percentage"):
        assert cs2_lvl10.progress_percentage(2500) is None

    with pytest.warns(UserWarning, match="is out of range"):
        assert cs2_lvl1.progress_percentage(600) is None


def test_int_conversion(cs2_lvl1: SkillLevel) -> None:
    assert int(cs2_lvl1) == 1


def test_equality(cs2_lvl1: SkillLevel) -> None:
    same_lvl1 = SkillLevel.get_level(GameID.CS2, 1)
    assert cs2_lvl1 == same_lvl1
    assert cs2_lvl1 is same_lvl1
    assert hash(cs2_lvl1) == hash(same_lvl1)


def test_inequality(
    cs2_lvl1: SkillLevel, cs2_lvl2: SkillLevel, csgo_lvl1: SkillLevel
) -> None:
    assert cs2_lvl1 != cs2_lvl2
    assert cs2_lvl1 != csgo_lvl1


def test_less_than(cs2_lvl1: SkillLevel, cs2_lvl2: SkillLevel) -> None:
    assert cs2_lvl1 < cs2_lvl2
    assert not (cs2_lvl2 < cs2_lvl1)


def test_total_ordering_methods(cs2_lvl1: SkillLevel, cs2_lvl2: SkillLevel) -> None:
    assert cs2_lvl2 > cs2_lvl1
    assert cs2_lvl1 <= cs2_lvl2
    assert cs2_lvl2 >= cs2_lvl1


def test_different_games_comparison_raises_error(
    cs2_lvl1: SkillLevel, csgo_lvl1: SkillLevel
) -> None:
    with pytest.raises(TypeError, match="Cannot compare levels from different games"):
        _ = cs2_lvl1 < csgo_lvl1

    with pytest.raises(TypeError):
        _ = cs2_lvl1 >= csgo_lvl1


def test_comparison_with_other_types(cs2_lvl1: SkillLevel) -> None:
    assert cs2_lvl1 != "level 1"
    assert cs2_lvl1 != 1
    with pytest.raises(TypeError):
        assert cs2_lvl1 < 5


def test_sorting() -> None:
    levels = SkillLevel.get_all_levels(GameID.CS2)
    shuffled = sorted(levels, key=lambda x: x.level, reverse=True)
    shuffled.sort()
    assert shuffled == levels
    assert all(shuffled[i] < shuffled[i + 1] for i in range(len(shuffled) - 1))
