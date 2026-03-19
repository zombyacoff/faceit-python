import pytest
from faceit import SkillLevel, GameID


class TestSkillLevelComparison:
    @pytest.fixture
    def cs2_lvl1(self):
        return SkillLevel.get_level(GameID.CS2, level=1)

    @pytest.fixture
    def cs2_lvl2(self):
        return SkillLevel.get_level(GameID.CS2, level=2)

    @pytest.fixture
    def csgo_lvl1(self):
        return SkillLevel.get_level(GameID.CSGO, level=1)

    def test_equality(self, cs2_lvl1):
        same_lvl1 = SkillLevel.get_level(GameID.CS2, level=1)
        assert cs2_lvl1 == same_lvl1
        assert cs2_lvl1 is same_lvl1
        assert hash(cs2_lvl1) == hash(same_lvl1)

    def test_inequality(self, cs2_lvl1, cs2_lvl2, csgo_lvl1):
        assert cs2_lvl1 != cs2_lvl2
        assert cs2_lvl1 != csgo_lvl1

    def test_less_than(self, cs2_lvl1, cs2_lvl2):
        assert cs2_lvl1 < cs2_lvl2
        assert not (cs2_lvl2 < cs2_lvl1)

    def test_total_ordering_methods(self, cs2_lvl1, cs2_lvl2):
        assert cs2_lvl2 > cs2_lvl1
        assert cs2_lvl1 <= cs2_lvl2
        assert cs2_lvl2 >= cs2_lvl1
        assert cs2_lvl1 <= cs2_lvl1

    def test_different_games_comparison_raises_error(self, cs2_lvl1, csgo_lvl1):
        with pytest.raises(
            TypeError, match="Cannot compare levels from different games"
        ):
            _ = cs2_lvl1 < csgo_lvl1

        with pytest.raises(TypeError):
            _ = cs2_lvl1 >= csgo_lvl1

    def test_comparison_with_other_types(self, cs2_lvl1):
        assert cs2_lvl1 != "level 1"
        assert cs2_lvl1 != 1
        with pytest.raises(TypeError):
            assert cs2_lvl1 < 5

    def test_sorting(self):
        levels = SkillLevel.get_all_levels(GameID.CS2)
        shuffled = sorted(levels, key=lambda x: x.level, reverse=True)
        shuffled.sort()
        assert shuffled == levels
        assert all(shuffled[i] < shuffled[i + 1] for i in range(len(shuffled) - 1))
