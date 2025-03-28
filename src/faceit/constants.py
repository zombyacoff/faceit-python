from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from typing import ClassVar, Dict, Final, List, Literal, NamedTuple, Optional, Union, cast, final, overload

from strenum import StrEnum

from .types import TypeAlias

_logger = logging.getLogger(__name__)

BASE_WIKI_URL: Final = "https://docs.faceit.com"

RAW_RESPONSE_ITEMS_KEY: Final = "items"
"""Key used to access items collection in API response data."""


class FaceitStrEnum(StrEnum):
    @classmethod
    def values(cls) -> List[str]:
        return [member.value for member in cls]


class GameID(FaceitStrEnum):
    APEX = "apex"
    BATTALION = "battalion"
    BRAWL_STARS = "brawl_stars"
    # BRAWL_STARS_AUTO = "brawl_stars_auto" deprecated
    CALL_OF_DUTY_MOBILE = "call-of-duty-mobile"
    CSGO = "csgo"
    CS2 = "cs2"
    CSDZ = "csdz"
    CODBO6 = "codbo6"
    COD_MW3 = "cod-mw3"
    COD_WZ = "cod-wz"
    CLASH_OF_CLANS = "clash-of-clans"
    CLASH_ROYALE = "clash_royale"
    # CLASH_ROYALE_AUTO = "clash_royale_auto" deprecated
    DEADLOCK = "deadlock"
    DESTINY2 = "destiny2"
    DESTINY2_PARENT = "destiny2_parent"
    DESTINY2_PS4 = "destiny2_ps4"
    DESTINY2_XBOX = "destiny2_xbox"
    DOTA2 = "dota2"
    DIRTYBOMB = "dirtybomb"
    EASPORTSCOLLEGEFOOTBALL25 = "easportscollegefootball25"
    EASPORTSFC24 = "easportsfc24"
    EASPORTSFC25 = "easportsfc25"
    EASPORTSNHL25 = "easportsnhl25"
    FALLGUYS = "fallguys"
    FIFA20 = "fifa20"
    FIFA22 = "fifa22"
    FIFA23 = "fifa23"
    FORTNITE = "fortnite"
    FC_MOBILE = "fc-mobile"
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
    # PUBGMOBILE_AUTO = "pubgmobile-auto" deprecated
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
    TEKKEN8 = "tekken8"
    TF2 = "tf2"
    TEAMFIGHT_TACTICS = "teamfight_tactics"
    TEMPERIA = "temperia"
    TRACKMANIA = "trackmania"
    UFC5 = "ufc-5"
    # VALORANT = "valorant" 4O4 ?
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


class EventStatus(FaceitStrEnum):
    ALL = "all"
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    PAST = "past"


class ExpandOption(FaceitStrEnum):
    NONE = ""
    ORGANIZER = "organizer"
    GAME = "game"


class Region(FaceitStrEnum):
    EU = "EU"
    US = "US"
    SEA = "SEA"
    OCEANIA = "Oceania"
    SA = "SA"


_ChallengerLevel: TypeAlias = Literal["challenger"]

# Maybe it's worth creating a `ChallengerLevel` class that would determine ELO up to #1000
# (by game->region, but region complicates this task; we can think about it,
# but it seems to me that this is not possible, unfortunately...)
CHALLENGER_LEVEL: Final = "challenger"
"""Elite tier reserved for `top 1000` players per `game`/`region`.

This rank represents a dynamic threshold based on leaderboard position rather than a fixed ELO value.
Due to its relative nature, determining Challenger status requires additional processing (leaderboard
position analysis by region) beyond standard ELO calculations. In our implementation, players with
actual Challenger status will be classified as level 10 for system consistency.

The constant is primarily defined for completeness in representing FACEIT's full ranking system
and may be utilized in future enhancements for precise leaderboard position tracking.
"""


class EloRange(NamedTuple):
    lower: int
    # `Optional` - because "challenger" (>#1000) might not be present in all disciplines
    upper: Optional[Union[int, _ChallengerLevel]]

    @property
    def is_open_ended(self) -> bool:
        return self.upper == CHALLENGER_LEVEL or self.upper is None

    def __str__(self) -> str:
        if self.is_open_ended:
            return f"{self.lower}+"
        return f"{self.lower}-{self.upper}"

    @property
    def size(self) -> Optional[int]:
        if self.is_open_ended:
            return None
        return cast(int, self.upper) - self.lower + 1

    def contains(self, elo: int) -> bool:
        if self.upper == CHALLENGER_LEVEL or self.upper is None:
            return elo >= self.lower
        return self.lower <= elo <= cast(int, self.upper)


_EloThreshold: TypeAlias = Dict[int, EloRange]

_DEFAULT_FIRST_ELO_RANGE: Final = EloRange(100, 800)
_DEFAULT_TEN_LEVEL_LOWER: Final = 2001


def _create_default_elo_tiers() -> _EloThreshold:
    tier_ranges = {1: _DEFAULT_FIRST_ELO_RANGE}
    for level in range(2, 10):
        # `cast(int, ...)` tells the type checker that we know `upper` is definitely an `int`
        # for levels 1-9, not the full Optional[Union[int, _ChallengerLevel]] type
        lower_bound = cast(int, tier_ranges[level - 1].upper) + 1
        tier_ranges[level] = EloRange(lower_bound, lower_bound + 149)

    return tier_ranges


_BASE_ELO_RANGES: Final = _create_default_elo_tiers()


def _append_elite_tier(
    elite_upper_bound: Optional[_ChallengerLevel], base_tiers: _EloThreshold = _BASE_ELO_RANGES
) -> _EloThreshold:
    return {**base_tiers, 10: EloRange(_DEFAULT_TEN_LEVEL_LOWER, elite_upper_bound)}


CHALLENGER_CAPPED_ELO_RANGES: Final = _append_elite_tier(CHALLENGER_LEVEL)
# Pre-generating this range configuration for future implementation needs
OPEN_ENDED_ELO_RANGES: Final = _append_elite_tier(None)

_EloThresholds: TypeAlias = Dict[GameID, _EloThreshold]

# fmt: off
ELO_THRESHOLDS: Final[_EloThresholds] = {
    GameID.CS2: {
        1: EloRange(100, 500), 2: EloRange(501, 750), 3: EloRange(751, 900),
        4: EloRange(901, 1050), 5: EloRange(1051, 1200), 6: EloRange(1201, 1350),
        7: EloRange(1351, 1530), 8: EloRange(1531, 1750), 9: EloRange(1751, 2000),
        10: EloRange(_DEFAULT_TEN_LEVEL_LOWER, CHALLENGER_LEVEL)
    },
    # These default ELO ranges (level 1: up to 800, subsequent levels: +150) are standard across most games
    # with few exceptions. CS2 demonstrates one such exception where FACEIT adjusted boundaries
    # following the major update, even during its beta phase. This implementation accounts for
    # both standard patterns and known variations in the platform's ranking system
    GameID.CSGO: CHALLENGER_CAPPED_ELO_RANGES,
    # TODO: Add more games (e.g. Dota 2)
}
# fmt: on


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SkillLevel:
    level: int
    game_id: GameID
    elo_range: EloRange
    name: str

    _registry: ClassVar[Dict[GameID, Dict[int, SkillLevel]]] = {}
    _initialized: ClassVar[bool] = False

    def __str__(self) -> str:
        return f"{self.name} ({self.elo_range})"

    @property
    def is_highest_level(self) -> bool:
        return self.elo_range.is_open_ended

    @property
    def range_size(self) -> Optional[int]:
        return self.elo_range.size

    @property
    def elo_needed_for_next_level(self) -> Optional[int]:
        if self.is_highest_level:
            return None

        next_level = self.get_next_level()
        if next_level is None:
            return None

        return next_level.elo_range.lower - self.elo_range.lower

    def contains_elo(self, elo: int, /) -> bool:
        return self.elo_range.contains(elo)

    def progress_percentage(self, elo: int) -> Optional[float]:
        if self.is_highest_level:
            warnings.warn("Cannot calculate progress percentage for highest level", UserWarning, stacklevel=2)
            return None

        if not self.contains_elo(elo):
            warnings.warn(f"Elo {elo} is out of range", UserWarning, stacklevel=2)
            return None

        return ((elo - self.elo_range.lower) / (cast(int, self.elo_range.upper) - self.elo_range.lower)) * 100

    def get_next_level(self) -> Optional[SkillLevel]:
        if self.is_highest_level:
            return None
        return self.get_level(self.game_id, self.level + 1)

    def get_previous_level(self) -> Optional[SkillLevel]:
        if self.level <= 1:
            return None
        return self.get_level(self.game_id, self.level - 1)

    @overload
    @classmethod
    def get_level(cls, game_id: GameID, level: int) -> Optional[SkillLevel]: ...
    @overload
    @classmethod
    def get_level(cls, game_id: GameID, *, elo: int) -> Optional[SkillLevel]: ...
    @classmethod
    def get_level(
        cls, game_id: GameID, level: Optional[int] = None, *, elo: Optional[int] = None
    ) -> Optional[SkillLevel]:
        cls._ensure_initialized()

        if game_id not in cls._registry:
            _logger.warning("Game '%s' is not supported", game_id)
            return None

        if elo is not None:
            _logger.debug("Getting level for game %s and elo %s", game_id, elo)
            return next((lvl for lvl in cls._registry[game_id].values() if lvl.contains_elo(elo)), None)

        if level is not None:
            _logger.debug("Getting level %s for game %s", level, game_id)
            return cls._registry.get(game_id, {}).get(level)

        warnings.warn("Please provide either level or elo", UserWarning, stacklevel=2)
        return None

    @classmethod
    def get_all_levels(cls, game_id: GameID) -> List[SkillLevel]:
        cls._ensure_initialized()
        return sorted(cls._registry.get(game_id, {}).values(), key=lambda x: x.level)

    @classmethod
    def _ensure_initialized(cls) -> None:
        if cls._initialized:
            return

        for game_id, thresholds in ELO_THRESHOLDS.items():
            if game_id not in cls._registry:
                cls._registry[game_id] = {}

            for level_num, elo_range in thresholds.items():
                cls._registry[game_id][level_num] = cls(
                    level=level_num, game_id=game_id, elo_range=elo_range, name=f"Level {level_num}"
                )

        cls._initialized = True

    @classmethod
    def reset_registry(cls) -> None:
        cls._registry.clear()
        cls._initialized = False


# Initialize the `SkillLevel` registry when the module is imported.
# This ensures all skill levels are available immediately without requiring explicit initialization.
# The registry contains all game skill levels mapped by game_id and level number.
SkillLevel._ensure_initialized()
