import typing
from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Annotated, TypeAlias

from faceit.constants import ELO_THRESHOLDS, GameID, SkillLevel
from faceit.models.custom_types import (
    FaceitID,
    LangFormattedAnyHttpUrl,
    ResponseContainer,
)
from faceit.types import AnyCSID, RawAPIItem, RegionIdentifier, UrlOrEmpty

_PlayerStatsT = typing.TypeVar("_PlayerStatsT", bound=GameID)
_SegmentStatsT = typing.TypeVar("_SegmentStatsT")
_LifetimeStatsT = typing.TypeVar("_LifetimeStatsT")

_SEGMENT_NAME: typing.Final = "label"


class MatchResult(IntEnum):
    LOSE = 0
    WIN = 1


class GameInfo(BaseModel):
    _SKILL_LVL: typing.ClassVar = "skill_level"

    region: RegionIdentifier
    game_player_id: str
    level: Annotated[typing.Union[int, SkillLevel], Field(alias=_SKILL_LVL)]
    elo: Annotated[int, Field(alias="faceit_elo")]
    game_player_name: str
    level_label: Annotated[str, Field("", alias="skill_level_label")]  # Maybe outdated
    regions: ResponseContainer[typing.Any]  # Maybe outdated
    game_profile_id: str

    @model_validator(mode="before")
    def _prepare_skill_level(cls, data: typing.Any) -> typing.Any:
        if not isinstance(data, dict):
            return data

        game_id = data.get(ResponseContainer._INJECTED_KEY)
        skill_lvl = data.get(cls._SKILL_LVL)

        if isinstance(skill_lvl, SkillLevel) or game_id is None or skill_lvl is None:
            return data
        if game_id not in ELO_THRESHOLDS:
            return data
        # NOTE: FACEIT returns level 0 for `GameID.CSGO`
        # (at least for 'm0NESY', discovered empirically; might apply to other games too),
        # which doesn't match any level in `ELO_THRESHOLDS`.
        # I assume this is an API bug caused by CSGO becoming obsolete after the release of CS2
        #
        # TODO: Understand why the API behaves this way
        if skill_lvl not in ELO_THRESHOLDS[game_id]:
            return data

        resolved = SkillLevel.get_level(game_id, skill_lvl)
        assert resolved is not None, (
            "`resolved` cannot be None because `game_id` was already validated "
            "to be present in `ELO_THRESHOLDS`"
        )
        data[cls._SKILL_LVL] = resolved
        return data


class PlayerSettings(BaseModel):
    language: str


class Player(BaseModel):
    id: Annotated[FaceitID, Field(alias="player_id")]
    nickname: str
    avatar: UrlOrEmpty
    country: str
    cover_image: UrlOrEmpty
    platforms: typing.Optional[ResponseContainer[str]]
    games: ResponseContainer[GameInfo]
    settings: PlayerSettings
    friends_ids: typing.List[FaceitID]
    new_steam_id: str
    steam_id_64: str
    steam_nickname: str
    memberships: typing.List[str]
    faceit_url: LangFormattedAnyHttpUrl
    membership_type: str
    cover_featured_image: UrlOrEmpty
    infractions: ResponseContainer[typing.Any]  # Maybe outdated
    verified: bool
    activated_at: datetime


class BanEntry(BaseModel):
    nickname: str
    type: str
    reason: str
    starts_at: datetime
    user_id: FaceitID


class Hub(BaseModel):
    id: Annotated[FaceitID, Field(alias="hub_id")]
    name: str
    avatar: UrlOrEmpty
    game_id: GameID
    organizer_id: FaceitID
    faceit_url: LangFormattedAnyHttpUrl


class GeneralTeam(BaseModel):
    id: Annotated[FaceitID, Field(alias="team_id")]
    nickname: str
    name: str
    avatar: UrlOrEmpty
    cover_image: typing.Optional[str] = None
    game: GameID
    type: Annotated[str, Field(alias="team_type")]
    members: typing.Optional[typing.List[str]] = None  # Maybe `List[Player]`?
    leader_id: Annotated[FaceitID, Field(alias="leader")]
    chat_room_id: str  # To be honest, I'm not totally sure what the ID is
    faceit_url: LangFormattedAnyHttpUrl


class Tournament(BaseModel):
    id: Annotated[FaceitID, Field(alias="tournament_id")]
    name: str
    featured_image: UrlOrEmpty  # Maybe just `str`
    game_id: GameID
    region: RegionIdentifier
    status: str
    custom: bool
    invite_type: str
    prize_type: str
    total_prize: str
    team_size: int
    min_skill: int
    max_skill: int
    match_type: str
    organizer_id: str
    whitelist_countries: typing.List[str]
    membership_type: str
    number_of_players: int
    number_of_players_joined: int
    number_of_players_checkedin: int
    number_of_players_participants: int
    anticheat_required: bool
    started_at: int
    subscriptions_count: int
    faceit_url: LangFormattedAnyHttpUrl


class CSLifetimeStats(BaseModel):  # `GameID.CS2` & `GameID.CSGO`
    adr: Annotated[float, Field(0, alias="ADR")]
    average_headshots_percentage: Annotated[int, Field(alias="Average Headshots %")]
    average_kd_ratio: Annotated[float, Field(alias="Average K/D Ratio")]
    current_win_streak: Annotated[int, Field(alias="Current Win Streak")]
    enemies_flashed_per_round: Annotated[
        float, Field(0.0, alias="Enemies Flashed per Round")
    ]
    entry_rate: Annotated[float, Field(0.0, alias="Entry Rate")]
    entry_success_rate: Annotated[float, Field(0.0, alias="Entry Success Rate")]
    flash_success_rate: Annotated[float, Field(0.0, alias="Flash Success Rate")]
    flashes_per_round: Annotated[float, Field(0.0, alias="Flashes per Round")]
    kd_ratio: Annotated[float, Field(alias="K/D Ratio")]
    longest_win_streak: Annotated[int, Field(alias="Longest Win Streak")]
    matches: Annotated[int, Field(alias="Matches")]
    recent_results: Annotated[
        typing.List[MatchResult], Field(alias="Recent Results", max_length=5)
    ]
    sniper_kill_rate: Annotated[float, Field(0.0, alias="Sniper Kill Rate")]
    sniper_kill_rate_per_round: Annotated[
        float, Field(0.0, alias="Sniper Kill Rate per Round")
    ]
    total_1v1_count: Annotated[int, Field(0, alias="Total 1v1 Count")]
    total_1v1_wins: Annotated[int, Field(0, alias="Total 1v1 Wins")]
    total_1v2_count: Annotated[int, Field(0, alias="Total 1v2 Count")]
    total_1v2_wins: Annotated[int, Field(0, alias="Total 1v2 Wins")]
    total_damage: Annotated[int, Field(0, alias="Total Damage")]
    total_enemies_flashed: Annotated[int, Field(0, alias="Total Enemies Flashed")]
    total_entry_count: Annotated[int, Field(0, alias="Total Entry Count")]
    total_entry_wins: Annotated[int, Field(0, alias="Total Entry Wins")]
    total_flash_count: Annotated[int, Field(0, alias="Total Flash Count")]
    total_flash_successes: Annotated[int, Field(0, alias="Total Flash Successes")]
    total_headshots_percentage: Annotated[int, Field(alias="Total Headshots %")]
    total_kills_with_extended_stats: Annotated[
        int, Field(0, alias="Total Kills with extended stats")
    ]
    total_matches: Annotated[int, Field(0, alias="Total Matches")]
    total_rounds_with_extended_stats: Annotated[
        int, Field(0, alias="Total Rounds with extended stats")
    ]
    total_sniper_kills: Annotated[int, Field(0, alias="Total Sniper Kills")]
    total_utility_count: Annotated[int, Field(0, alias="Total Utility Count")]
    total_utility_damage: Annotated[int, Field(0, alias="Total Utility Damage")]
    total_utility_successes: Annotated[int, Field(0, alias="Total Utility Successes")]
    utility_damage_per_round: Annotated[
        float, Field(0.0, alias="Utility Damage per Round")
    ]
    utility_damage_success_rate: Annotated[
        float, Field(0.0, alias="Utility Damage Success Rate")
    ]
    utility_success_rate: Annotated[float, Field(0.0, alias="Utility Success Rate")]
    utility_usage_per_round: Annotated[
        float, Field(0.0, alias="Utility Usage per Round")
    ]
    v1_win_rate: Annotated[float, Field(0.0, alias="1v1 Win Rate")]
    v2_win_rate: Annotated[float, Field(0.0, alias="1v2 Win Rate")]
    win_rate: Annotated[int, Field(alias="Win Rate %")]  # in percentage
    wins: Annotated[int, Field(alias="Wins")]


class CSMapStats(BaseModel):  # `GameID.CS2` & `GameID.CSGO`
    # TODO: Преобразование в проценты (*100) таких полей, как "v2_win_rate", "v1_win_rate", ... ?
    adr: Annotated[float, Field(0.0, alias="ADR")]
    assists: Annotated[int, Field(alias="Assists")]
    average_assists: Annotated[float, Field(alias="Average Assists")]
    average_deaths: Annotated[float, Field(alias="Average Deaths")]
    average_headshots_percentage: Annotated[float, Field(alias="Average Headshots %")]
    average_kd_ratio: Annotated[float, Field(alias="Average K/D Ratio")]
    average_kills: Annotated[float, Field(alias="Average Kills")]
    average_kr_ratio: Annotated[float, Field(alias="Average K/R Ratio")]
    average_mvps: Annotated[float, Field(alias="Average MVPs")]
    average_penta_kills: Annotated[float, Field(alias="Average Penta Kills")]
    average_quadro_kills: Annotated[float, Field(alias="Average Quadro Kills")]
    average_triple_kills: Annotated[float, Field(alias="Average Triple Kills")]
    deaths: Annotated[int, Field(alias="Deaths")]
    enemies_flashed_per_round: Annotated[
        float, Field(0.0, alias="Enemies Flashed per Round")
    ]
    entry_rate: Annotated[float, Field(0.0, alias="Entry Rate")]
    entry_success_rate: Annotated[float, Field(0.0, alias="Entry Success Rate")]
    flash_success_rate: Annotated[float, Field(0.0, alias="Flash Success Rate")]
    flashes_per_round: Annotated[float, Field(0.0, alias="Flashes per Round")]
    headshots: Annotated[int, Field(alias="Headshots")]
    headshots_per_match: Annotated[float, Field(alias="Headshots per Match")]
    kd_ratio: Annotated[float, Field(alias="K/D Ratio")]
    kills: Annotated[int, Field(alias="Kills")]
    kr_ratio: Annotated[float, Field(alias="K/R Ratio")]
    matches: Annotated[int, Field(alias="Matches")]
    mvps: Annotated[int, Field(alias="MVPs")]
    penta_kills: Annotated[int, Field(alias="Penta Kills")]
    quadro_kills: Annotated[int, Field(alias="Quadro Kills")]
    rounds: Annotated[int, Field(alias="Rounds")]
    sniper_kill_rate: Annotated[float, Field(0.0, alias="Sniper Kill Rate")]
    sniper_kill_rate_per_round: Annotated[
        float, Field(0.0, alias="Sniper Kill Rate per Round")
    ]
    total_1v1_count: Annotated[int, Field(0, alias="Total 1v1 Count")]
    total_1v1_wins: Annotated[int, Field(0, alias="Total 1v1 Wins")]
    total_1v2_count: Annotated[int, Field(0, alias="Total 1v2 Count")]
    total_1v2_wins: Annotated[int, Field(0, alias="Total 1v2 Wins")]
    total_damage: Annotated[int, Field(0, alias="Total Damage")]
    total_enemies_flashed: Annotated[int, Field(0, alias="Total Enemies Flashed")]
    total_entry_count: Annotated[int, Field(0, alias="Total Entry Count")]
    total_entry_wins: Annotated[int, Field(0, alias="Total Entry Wins")]
    total_flash_count: Annotated[int, Field(0, alias="Total Flash Count")]
    total_flash_successes: Annotated[int, Field(0, alias="Total Flash Successes")]
    total_headshots_percentage: Annotated[int, Field(alias="Total Headshots %")]
    total_kills_with_extended_stats: Annotated[
        int, Field(0, alias="Total Kills with extended stats")
    ]
    total_matches: Annotated[int, Field(0, alias="Total Matches")]
    total_rounds_with_extended_stats: Annotated[
        int, Field(0, alias="Total Rounds with extended stats")
    ]
    total_sniper_kills: Annotated[int, Field(0, alias="Total Sniper Kills")]
    total_utility_count: Annotated[int, Field(0, alias="Total Utility Count")]
    total_utility_damage: Annotated[int, Field(0, alias="Total Utility Damage")]
    total_utility_successes: Annotated[int, Field(0, alias="Total Utility Successes")]
    triple_kills: Annotated[int, Field(alias="Triple Kills")]
    utility_damage_per_round: Annotated[
        float, Field(0.0, alias="Utility Damage per Round")
    ]
    utility_damage_success_rate: Annotated[
        float, Field(0.0, alias="Utility Damage Success Rate")
    ]
    utility_success_rate: Annotated[float, Field(0.0, alias="Utility Success Rate")]
    utility_usage_per_round: Annotated[
        float, Field(0.0, alias="Utility Usage per Round")
    ]
    v1_win_rate: Annotated[float, Field(0.0, alias="1v1 Win Rate")]
    v2_win_rate: Annotated[float, Field(0.0, alias="1v2 Win Rate")]
    win_rate: Annotated[int, Field(alias="Win Rate %")]
    wins: Annotated[int, Field(alias="Wins")]


class Segment(BaseModel, typing.Generic[_SegmentStatsT]):
    stats: _SegmentStatsT
    type: str
    mode: str
    name: Annotated[str, Field(alias=_SEGMENT_NAME)]
    img_small: UrlOrEmpty
    img_regular: UrlOrEmpty


class PlayerStats(
    # TODO: Подумать над более элегантной типизацией в зависимости от `GameID`
    BaseModel,
    typing.Generic[
        _PlayerStatsT,
        _LifetimeStatsT,
        _SegmentStatsT,
    ],
):
    id: Annotated[FaceitID, Field(alias="player_id")]
    game_id: _PlayerStatsT
    lifetime: _LifetimeStatsT  # Относительно `game_id`; для иных игр модели делать не собираюсь
    segments: ResponseContainer[
        Segment[_SegmentStatsT]
    ]  # TODO: Add description; usage guide

    @model_validator(mode="before")
    def _prepare_segments(cls, data: typing.Any) -> typing.Any:
        if not isinstance(data, dict):
            return data

        raw_segments = data.get("segments")
        if isinstance(raw_segments, list):
            data["segments"] = {
                # NOTE: Anubis --> anubis, Ancient --> ancient, ...
                # (lowercase and replace spaces with underscores)
                seg.get(_SEGMENT_NAME).lower().replace(" ", "_"): seg
                for seg in raw_segments
                if _SEGMENT_NAME in seg
            }

        return data


CSPlayerStats: TypeAlias = PlayerStats[
    AnyCSID,
    CSLifetimeStats,
    CSMapStats,
]

FallbackPlayerStats: TypeAlias = PlayerStats[
    GameID,
    RawAPIItem,
    RawAPIItem,
]

AnyPlayerStats: TypeAlias = typing.Union[
    CSPlayerStats,
    FallbackPlayerStats,
]
