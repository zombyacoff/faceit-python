from __future__ import annotations

import logging
import typing as t
from dataclasses import dataclass
from operator import attrgetter
from warnings import warn

from pydantic import Field, validate_call
from strenum import StrEnum

from ._typing import TypeAlias, deprecated
from ._utils import StrEnumWithAll

if t.TYPE_CHECKING:
    _EloThreshold: TypeAlias = t.Dict[int, "EloRange"]

_logger = logging.getLogger(__name__)

BASE_WIKI_URL: t.Final = "https://docs.faceit.com"

RAW_RESPONSE_ITEMS_KEY: t.Final = "items"

MIN_ELO: t.Final = 100
"""Minimum ELO value across all FACEIT games.

Players cannot drop below this threshold regardless of consecutive losses.
"""


class EventCategory(StrEnum):
    ALL = "all"
    ONGOING = "ongoing"
    PAST = "past"
    UPCOMING = "upcoming"


class ExpandedField(StrEnumWithAll):
    GAME = "game"
    ORGANIZER = "organizer"


@deprecated("Use ExpandedField instead")
class ExpandOption(StrEnumWithAll):
    NONE = ""
    GAME = "game"
    ORGANIZER = "organizer"


class GameID(StrEnum):
    APEX = "apex"
    BATTALION = "battalion"
    BRAWL_STARS = "brawl_stars"
    CALL_OF_DUTY_MOBILE = "call-of-duty-mobile"
    CLASH_OF_CLANS = "clash-of-clans"
    CLASH_ROYALE = "clash_royale"
    CODBO6 = "codbo6"
    COD_MW3 = "cod-mw3"
    COD_WZ = "cod-wz"
    CS2 = "cs2"
    CSDZ = "csdz"
    CSGO = "csgo"
    DEADLOCK = "deadlock"
    DESTINY2 = "destiny2"
    DESTINY2_PARENT = "destiny2_parent"
    DESTINY2_PS4 = "destiny2_ps4"
    DESTINY2_XBOX = "destiny2_xbox"
    DIRTYBOMB = "dirtybomb"
    DOTA2 = "dota2"
    EASPORTSCOLLEGEFOOTBALL25 = "easportscollegefootball25"
    EASPORTSFC24 = "easportsfc24"
    EASPORTSFC25 = "easportsfc25"
    EASPORTSNHL25 = "easportsnhl25"
    FALLGUYS = "fallguys"
    FC_MOBILE = "fc-mobile"
    FIFA20 = "fifa20"
    FIFA22 = "fifa22"
    FIFA23 = "fifa23"
    FORTNITE = "fortnite"
    FREEFIRE = "freefire"
    GS_RAINBOW6_PS4 = "gs_rainbow_6_ps4"
    GS_RAINBOW6_XBOX = "gs_rainbow_6_xbox"
    HALO3 = "halo_3"
    HALO5 = "halo_5"
    HALO_INFINITE = "halo_infinite"
    HALO_MCC = "halo_mcc"
    HEARTHSTONE = "hearthstone"
    HEARTHSTONE_BATTLEGROUNDS = "hearthstone-battlegrounds"
    KRUNKER = "krunker"
    LOL_BR = "lol_BR"
    LOL_EUN = "lol_EUN"
    LOL_EUW = "lol_EUW"
    LOL_LAN = "lol_LAN"
    LOL_LAS = "lol_LAS"
    LOL_NA = "lol_NA"
    LOL_OCE = "lol_OCE"
    LOL_PARENT = "lol_parent"
    LOL_TR = "lol_TR"
    MADDEN25 = "madden25"
    MLBTHESHOW24 = "mlbtheshow24"
    MINION_MASTERS = "minion_masters"
    MLBB = "mlbb"
    NBA2K25 = "nba2k25"
    NEWSTATE = "newstate"
    NHL18_PS4 = "nhl_18_PS4"
    NHL18_XBOX = "nhl_18_XBOX"
    NHL19 = "nhl_19"
    NHL19_PS4 = "nhl_19_PS4"
    NHL19_XBOX = "nhl_19_XBOX"
    NHL20_PARENT = "nhl_20_parent"
    NHL20_PS4 = "nhl_20_ps4"
    NHL20_XBOX = "nhl_20_xbox"
    OVERWATCH = "overwatch"
    OVERWATCH_EU = "overwatch_EU"
    OVERWATCH_KR = "overwatch_KR"
    OVERWATCH_US = "overwatch_US"
    OVERWATCH2 = "ow2"
    PUBG = "pubg"
    PUBGMOBILE = "pubgmobile"
    QUAKE_CHAMPIONS = "quake_champions"
    RAINBOW6 = "rainbow_6"
    RL_XBOX_PC = "rl_XBOX_PC"
    RING_OF_ELYSIUM = "ring_of_elysium"
    ROCKET_LEAGUE = "rocket_league"
    SKILL_SPECIAL_FORCE2 = "skill-special-force2"
    SMITE = "smite"
    SMITE_XBOX = "smite_xbox"
    SPLATOON3 = "splatoon-3"
    SQUADBLAST_BETA = "squadblast-beta"
    STARWARSJKJA = "starwarsjkja"
    TEAMFIGHT_TACTICS = "teamfight_tactics"
    TEKKEN8 = "tekken8"
    TEMPERIA = "temperia"
    TF2 = "tf2"
    TRACKMANIA = "trackmania"
    UFC5 = "ufc-5"
    VALORANT = "valorant"
    WARFACE = "warface"
    WARFACE_ALPHA = "warface_alpha"
    WARFACE_EU = "warface_eu"
    WARFACE_NA = "warface_na"
    WARFACE_PARENT = "warface_parent"
    WOT_EU = "wot_EU"
    WOT_NA = "wot_NA"
    WOT_RU = "wot_RU"
    WOT_XBOX = "wot_xbox"
    WOW = "wow"


class HighTierLevel(StrEnum):
    ABSENT = "absent"
    """Indicates the absence of a defined top-tier rank in this discipline.

    Used when there is no distinct elite or highest rank in the ranking structure.
    """

    CHALLENGER = "challenger"
    """Elite tier reserved for top 1000 players per game/region.

    This rank represents a dynamic threshold based on leaderboard position rather
    than a fixed ELO value. Due to its relative nature, determining Challenger
    status requires additional processing (leaderboard position analysis by region)
    beyond standard ELO calculations. In our implementation, players with actual
    Challenger status will be classified as level 10 for system consistency.

    The constant is primarily defined for completeness in representing FACEIT's
    full ranking system and may be utilized in future enhancements for precise
    leaderboard position tracking.
    """


class Region(StrEnum):
    EU = "EU"
    OCEANIA = "Ocenia"
    SA = "SA"
    SEA = "SEA"
    US = "US"


@t.final
class EloRange(t.NamedTuple):
    lower: int
    upper: t.Union[int, HighTierLevel]

    @property
    def is_open_ended(self) -> bool:
        return self.upper in HighTierLevel

    @property
    def size(self) -> t.Optional[int]:
        if self.is_open_ended:
            return None
        assert isinstance(self.upper, int)  # noqa: S101
        return self.upper - self.lower + 1

    def contains(self, elo: int) -> bool:
        if self.upper in HighTierLevel:
            return elo >= self.lower
        assert isinstance(self.upper, int)  # noqa: S101
        return self.lower <= elo <= self.upper

    def __str__(self) -> str:
        if self.is_open_ended:
            return f"{self.lower}+"
        return f"{self.lower}-{self.upper}"


_DEFAULT_FIRST_ELO_RANGE: t.Final = EloRange(MIN_ELO, 800)
_DEFAULT_TEN_LEVEL_LOWER: t.Final = 2001


def _create_default_elo_tiers() -> _EloThreshold:
    tier_ranges = {1: _DEFAULT_FIRST_ELO_RANGE}

    for level in range(2, 10):
        # `cast(int, ...)` tells the type checker that we know `upper` is
        # definitely an `int` for levels 1-9, not the full
        # `Optional[Union[int, Literal["challenger"]]` type
        lower_bound = t.cast(int, tier_ranges[level - 1].upper) + 1
        tier_ranges[level] = EloRange(lower_bound, lower_bound + 149)

    return tier_ranges


_BASE_ELO_RANGES: t.Final = _create_default_elo_tiers()


def _append_elite_tier(
    elite_upper_bound: HighTierLevel,
    base_tiers: _EloThreshold = _BASE_ELO_RANGES,
    /,
) -> _EloThreshold:
    return {
        **base_tiers,
        10: EloRange(_DEFAULT_TEN_LEVEL_LOWER, elite_upper_bound),
    }


CHALLENGER_CAPPED_ELO_RANGES: t.Final = _append_elite_tier(
    HighTierLevel.CHALLENGER
)
# Pre-generating this range configuration for future implementation needs
# Exposed as a constant for both internal use and potential library consumers
OPEN_ENDED_ELO_RANGES: t.Final = _append_elite_tier(HighTierLevel.ABSENT)

# fmt: off
ELO_THRESHOLDS: t.Final[t.Dict[GameID, _EloThreshold]] = {
    GameID.CS2: {
        1: EloRange(MIN_ELO, 500), 2: EloRange(501, 750), 3: EloRange(751, 900),
        4: EloRange(901, 1050), 5: EloRange(1051, 1200), 6: EloRange(1201, 1350),
        7: EloRange(1351, 1530), 8: EloRange(1531, 1750), 9: EloRange(1751, 2000),
        10: EloRange(_DEFAULT_TEN_LEVEL_LOWER, HighTierLevel.CHALLENGER)
    },
    # These default ELO ranges (level 1: up to 800, subsequent levels: +150) are
    # standard across most games with few exceptions. CS2 demonstrates one such
    # exception where FACEIT adjusted boundaries following the transition from
    # CSGO. This implementation accounts for both standard patterns and known
    # variations in the platform's ranking system
    GameID.CSGO: CHALLENGER_CAPPED_ELO_RANGES,
    # TODO: Add more games (e.g. Dota 2)
}
# fmt: on


@t.final
@dataclass(frozen=True)
class SkillLevel:
    __slots__ = ("elo_range", "game_id", "level", "name")

    level: int
    game_id: GameID
    elo_range: EloRange
    name: str

    _registry: t.ClassVar[t.Dict[GameID, t.Dict[int, SkillLevel]]] = {}

    @property
    def is_highest_level(self) -> bool:
        return self.elo_range.is_open_ended

    @property
    def range_size(self) -> t.Optional[int]:
        return self.elo_range.size

    @property
    def next_level(self) -> t.Optional[SkillLevel]:
        if self.is_highest_level:
            return None
        return self.get_level(self.game_id, self.level + 1)

    @property
    def previous_level(self) -> t.Optional[SkillLevel]:
        if self.level <= 1:
            return None
        return self.get_level(self.game_id, self.level - 1)

    @property
    def elo_needed_for_next_level(self) -> t.Optional[int]:
        if self.is_highest_level:
            return None

        next_level = self.next_level
        if next_level is None:
            return None

        return next_level.elo_range.lower - self.elo_range.lower

    def contains_elo(self, elo: int, /) -> bool:
        return self.elo_range.contains(elo)

    @validate_call
    def progress_percentage(
        self, elo: int = Field(ge=MIN_ELO), /
    ) -> t.Optional[float]:
        if self.is_highest_level:
            warn(
                "Cannot calculate progress percentage for highest level",
                UserWarning,
                stacklevel=4,
            )
            return None

        if not self.contains_elo(elo):
            warn(f"Elo {elo} is out of range", UserWarning, stacklevel=4)
            return None

        assert isinstance(self.elo_range.upper, int)  # noqa: S101
        return (
            (elo - self.elo_range.lower)
            / (self.elo_range.upper - self.elo_range.lower)
        ) * 100

    @t.overload
    @classmethod
    def get_level(
        cls,
        game_id: GameID,
        level: int = Field(ge=1, le=10),
    ) -> t.Optional[SkillLevel]: ...

    @t.overload
    @classmethod
    def get_level(
        cls, game_id: GameID, *, elo: int = Field(ge=MIN_ELO)
    ) -> t.Optional[SkillLevel]: ...

    @classmethod
    def get_level(
        cls,
        game_id: GameID,
        level: t.Optional[int] = Field(None, ge=1, le=10),
        *,
        elo: t.Optional[int] = Field(None, ge=MIN_ELO),
    ) -> t.Optional[SkillLevel]:
        if game_id not in cls._registry:
            warn(
                f"Game '{game_id}' is not supported", UserWarning, stacklevel=4
            )
            return None

        if level is not None and elo is not None:
            warn(
                "Both 'level' and 'elo' parameters provided; "
                "'level' takes precedence",
                UserWarning,
                stacklevel=4,
            )

        if level is not None:
            _logger.debug("Getting level %s for game %s", level, game_id)
            return cls._registry.get(game_id, {}).get(level)

        if elo is not None:
            _logger.debug("Getting level for game %s and elo %s", game_id, elo)
            return next(
                (
                    lvl
                    for lvl in cls._registry[game_id].values()
                    if lvl.contains_elo(elo)
                ),
                None,
            )

        raise ValueError("Either level or elo must be specified")

    @classmethod
    def get_all_levels(cls, game_id: GameID, /) -> t.List[SkillLevel]:
        return sorted(
            cls._registry.get(game_id, {}).values(), key=attrgetter("level")
        )

    def __int__(self) -> int:
        return self.level

    @classmethod
    def _initialize_skill_levels_registry(cls) -> None:
        cls._registry = {
            game_id: {
                level_num: cls(
                    level_num, game_id, elo_range, f"Level {level_num}"
                )
                for level_num, elo_range in thresholds.items()
            }
            for game_id, thresholds in ELO_THRESHOLDS.items()
        }


# We must wrap `get_level` and `get_all_levels` with `validate_call` after class creation
# because using `@validate_call` directly on classmethods with forward references
# (e.g., return type "SkillLevel") causes `NameError: the class is not yet defined`
# when Pydantic tries to resolve type annotations. Wrapping after definition
# ensures all references are resolvable and avoids import-time errors.
SkillLevel.get_level = validate_call(SkillLevel.get_level)  # type: ignore[method-assign]
SkillLevel.get_all_levels = validate_call(SkillLevel.get_all_levels)  # type: ignore[method-assign]

# Initialize the `SkillLevel` registry when the module is imported.
# This ensures all skill levels are available immediately without requiring
# explicit initialization. The registry contains all game skill levels mapped
# by game_id and level number.
SkillLevel._initialize_skill_levels_registry()

# Remove both constructor and initialization method after registry setup.
# This enforces the registry pattern where all valid `SkillLevel` instances
# are predefined, ensuring data integrity and preventing misuse of the class.
del SkillLevel.__init__
del SkillLevel._initialize_skill_levels_registry
