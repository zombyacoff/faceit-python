import typing as t
from datetime import datetime

import typing_extensions as te
from pydantic import BaseModel, Field

from faceit.constants import GameID, Region
from faceit.models.custom_types import (
    FaceitID,
    LangFormattedAnyHttpUrl,
    ResponseContainer,
)
from faceit.types import UrlOrEmpty


class GameInfo(BaseModel):
    region: Region
    game_player_id: str
    level: te.Annotated[int, Field(alias="skill_level")]
    elo: te.Annotated[int, Field(alias="faceit_elo")]
    game_player_name: str
    # This attribute appears to be te.deprecated and is no longer provided
    # by the API. Remove only if you have confirmed that "skill_level_label"
    # is not returned in any current responses.
    # level_label: str = Field(alias="skill_level_label")
    regions: ResponseContainer[Region] = ResponseContainer({})
    game_profile_id: str


class Player(BaseModel):
    id: te.Annotated[FaceitID, Field(alias="player_id")]
    nickname: str
    avatar: UrlOrEmpty
    country: str
    cover_image: UrlOrEmpty
    platforms: t.Optional[ResponseContainer[str]]
    games: ResponseContainer[GameInfo]
    settings: ResponseContainer
    friends_ids: t.List[FaceitID]
    new_steam_id: str
    steam_id_64: str
    steam_nickname: str
    memberships: t.List[str]
    faceit_url: LangFormattedAnyHttpUrl
    membership_type: str
    cover_featured_image: str
    infractions: ResponseContainer
    verified: bool
    activated_at: datetime


class BanEntry(BaseModel):
    nickname: str
    type: str
    reason: str
    starts_at: datetime
    user_id: FaceitID


class Hub(BaseModel):
    id: te.Annotated[FaceitID, Field(alias="hub_id")]
    name: str
    avatar: UrlOrEmpty
    game_id: GameID
    organizer_id: FaceitID
    faceit_url: LangFormattedAnyHttpUrl


class GeneralTeam(BaseModel):
    id: te.Annotated[FaceitID, Field(alias="team_id")]
    nickname: str
    name: str
    avatar: UrlOrEmpty
    cover_image: t.Optional[str] = None
    game: GameID
    type: te.Annotated[str, Field(alias="team_type")]
    members: t.Optional[t.List[str]] = None  # Maybe `List[Player]`?
    leader_id: te.Annotated[FaceitID, Field(alias="leader")]
    chat_room_id: str  # To be honest, I'm not totally sure what the ID is
    faceit_url: LangFormattedAnyHttpUrl


class Tournament(BaseModel):
    id: te.Annotated[FaceitID, Field(alias="tournament_id")]
    name: str
    featured_image: UrlOrEmpty  # Maybe just `str`
    game_id: GameID
    region: Region
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
    whitelist_countries: t.List[str]
    membership_type: str
    number_of_players: int
    number_of_players_joined: int
    number_of_players_checkedin: int
    number_of_players_participants: int
    anticheat_required: bool
    started_at: int
    subscriptions_count: int
    faceit_url: LangFormattedAnyHttpUrl


class LifetimeStats(BaseModel):
    # TODO
    total_1v1_wins: te.Annotated[str, Field(alias="Total 1v1 Wins")]
    win_rate: te.Annotated[str, Field(alias="Win Rate %")]
    total_sniper_kills: te.Annotated[str, Field(alias="Total Sniper Kills")]
    longest_win_streak: te.Annotated[str, Field(alias="Longest Win Streak")]
    flash_success_rate: te.Annotated[str, Field(alias="Flash Success Rate")]
    total_flash_count: te.Annotated[str, Field(alias="Total Flash Count")]
    utility_success_rate: te.Annotated[
        str, Field(alias="Utility Success Rate")
    ]
    total_damage: te.Annotated[str, Field(alias="Total Damage")]
    total_1v2_count: te.Annotated[str, Field(alias="Total 1v2 Count")]
    average_kd_ratio: te.Annotated[str, Field(alias="Average K/D Ratio")]
    wins: str
    sniper_kill_rate: te.Annotated[str, Field(alias="Sniper Kill Rate")]
    total_rounds_with_extended_stats: te.Annotated[
        str, Field(alias="Total Rounds with extended stats")
    ]
    kd_ratio: te.Annotated[str, Field(alias="K/D Ratio")]
    utility_damage_success_rate: te.Annotated[
        str, Field(alias="Utility Damage Success Rate")
    ]
    total_entry_count: te.Annotated[str, Field(alias="Total Entry Count")]
    average_headshots_percentage: te.Annotated[
        str, Field(alias="Average Headshots %")
    ]
    total_utility_successes: te.Annotated[
        str, Field(alias="Total Utility Successes")
    ]
    v2_win_rate: te.Annotated[str, Field(alias="1v2 Win Rate")]
    total_kills_with_extended_stats: te.Annotated[
        str, Field(alias="Total Kills with extended stats")
    ]
    matches: str
    entry_success_rate: te.Annotated[str, Field(alias="Entry Success Rate")]
    total_utility_damage: te.Annotated[
        str, Field(alias="Total Utility Damage")
    ]
    total_entry_wins: te.Annotated[str, Field(alias="Total Entry Wins")]
    current_win_streak: te.Annotated[str, Field(alias="Current Win Streak")]
    utility_usage_per_round: te.Annotated[
        str, Field(alias="Utility Usage per Round")
    ]
    recent_results: te.Annotated[t.List[str], Field(alias="Recent Results")]
    total_1v1_count: te.Annotated[str, Field(alias="Total 1v1 Count")]
    total_headshots_percentage: te.Annotated[
        str, Field(alias="Total Headshots %")
    ]
    enemies_flashed_per_round: te.Annotated[
        str, Field(alias="Enemies Flashed per Round")
    ]
    flashes_per_round: te.Annotated[str, Field(alias="Flashes per Round")]
    sniper_kill_rate_per_round: te.Annotated[
        str, Field(alias="Sniper Kill Rate per Round")
    ]
    adr: te.Annotated[str, Field(alias="ADR")]
    v1_win_rate: te.Annotated[str, Field(alias="1v1 Win Rate")]
    total_utility_count: te.Annotated[str, Field(alias="Total Utility Count")]
    total_flash_successes: te.Annotated[
        str, Field(alias="Total Flash Successes")
    ]
    total_1v2_wins: te.Annotated[str, Field(alias="Total 1v2 Wins")]
    total_matches: te.Annotated[str, Field(alias="Total Matches")]
    entry_rate: te.Annotated[str, Field(alias="Entry Rate")]
    total_enemies_flashed: te.Annotated[
        str, Field(alias="Total Enemies Flashed")
    ]
    utility_damage_per_round: te.Annotated[
        str, Field(alias="Utility Damage per Round")
    ]


class MapStats(BaseModel):
    # TODO значения по умолчанию для полей "_with_extended_stats" = None (или 0?),
    # так как они отсутсвтуют для старых матчей (предположу, что появились только в районе лета 2024)
    utility_success_rate: te.Annotated[
        float, Field(alias="Utility Success Rate")
    ]
    entry_success_rate: te.Annotated[float, Field(alias="Entry Success Rate")]
    total_entry_wins: te.Annotated[int, Field(alias="Total Entry Wins")]
    # NOTE посмотреть матчи за 2023 ?
    total_rounds_with_extended_stats: te.Annotated[
        int, Field(alias="Total Rounds with extended stats")
    ]
    deaths: te.Annotated[int, Field(alias="Deaths")]
    # TODO преобразование в проценты (*100) таких полей, как "v2_win_rate", "v1_win_rate", ...
    v2_win_rate: te.Annotated[float, Field(alias="1v2 Win Rate")]
    total_kills_with_extended_stats: te.Annotated[
        int, Field(alias="Total Kills with extended stats")
    ]
    v1_win_rate: te.Annotated[float, Field(alias="1v1 Win Rate")]
    total_enemies_flashed: te.Annotated[
        int, Field(alias="Total Enemies Flashed")
    ]
    mvps: te.Annotated[int, Field(alias="MVPs")]
    rounds: te.Annotated[int, Field(alias="Rounds")]
    average_assists: te.Annotated[float, Field(alias="Average Assists")]
    sniper_kill_rate: te.Annotated[float, Field(alias="Sniper Kill Rate")]

    # TODO корректную типизацию полей
    average_triple_kills: te.Annotated[
        str, Field(alias="Average Triple Kills")
    ]
    average_quadro_kills: te.Annotated[
        str, Field(alias="Average Quadro Kills")
    ]
    penta_kills: te.Annotated[str, Field(alias="Penta Kills")]
    total_flash_successes: te.Annotated[
        str, Field(alias="Total Flash Successes")
    ]
    average_headshots_percentage: te.Annotated[
        str, Field(alias="Average Headshots %")
    ]
    average_kd_ratio: te.Annotated[str, Field(alias="Average K/D Ratio")]
    enemies_flashed_per_round: te.Annotated[
        str, Field(alias="Enemies Flashed per Round")
    ]
    total_flash_count: te.Annotated[str, Field(alias="Total Flash Count")]
    quadro_kills: te.Annotated[str, Field(alias="Quadro Kills")]
    flashes_per_round: te.Annotated[str, Field(alias="Flashes per Round")]
    total_headshots_percentage: te.Annotated[
        str, Field(alias="Total Headshots %")
    ]
    total_1v1_wins: te.Annotated[str, Field(alias="Total 1v1 Wins")]
    average_deaths: te.Annotated[str, Field(alias="Average Deaths")]
    kills: te.Annotated[str, Field(alias="Kills")]
    flash_success_rate: te.Annotated[str, Field(alias="Flash Success Rate")]
    entry_rate: te.Annotated[str, Field(alias="Entry Rate")]
    sniper_kill_rate_per_round: te.Annotated[
        str, Field(alias="Sniper Kill Rate per Round")
    ]
    average_penta_kills: te.Annotated[str, Field(alias="Average Penta Kills")]
    headshots_per_match: te.Annotated[str, Field(alias="Headshots per Match")]
    adr: te.Annotated[str, Field(alias="ADR")]
    total_damage: te.Annotated[str, Field(alias="Total Damage")]
    total_utility_count: te.Annotated[str, Field(alias="Total Utility Count")]
    total_entry_count: te.Annotated[str, Field(alias="Total Entry Count")]
    wins: te.Annotated[str, Field(alias="Wins")]
    total_sniper_kills: te.Annotated[str, Field(alias="Total Sniper Kills")]
    total_1v2_wins: te.Annotated[str, Field(alias="Total 1v2 Wins")]
    headshots: te.Annotated[str, Field(alias="Headshots")]
    total_1v2_count: te.Annotated[str, Field(alias="Total 1v2 Count")]
    utility_usage_per_round: te.Annotated[
        str, Field(alias="Utility Usage per Round")
    ]
    total_utility_damage: te.Annotated[
        str, Field(alias="Total Utility Damage")
    ]
    kd_ratio: te.Annotated[str, Field(alias="K/D Ratio")]
    kr_ratio: te.Annotated[str, Field(alias="K/R Ratio")]
    average_kills: te.Annotated[str, Field(alias="Average Kills")]
    win_rate: te.Annotated[str, Field(alias="Win Rate %")]
    utility_damage_success_rate: te.Annotated[
        str, Field(alias="Utility Damage Success Rate")
    ]
    utility_damage_per_round: te.Annotated[
        str, Field(alias="Utility Damage per Round")
    ]
    total_utility_successes: te.Annotated[
        str, Field(alias="Total Utility Successes")
    ]
    matches: te.Annotated[str, Field(alias="Matches")]
    total_matches: te.Annotated[str, Field(alias="Total Matches")]
    average_mvps: te.Annotated[str, Field(alias="Average MVPs")]
    assists: te.Annotated[str, Field(alias="Assists")]
    total_1v1_count: te.Annotated[str, Field(alias="Total 1v1 Count")]
    triple_kills: te.Annotated[str, Field(alias="Triple Kills")]
    average_kr_ratio: te.Annotated[str, Field(alias="Average K/R Ratio")]


class MapSegment(BaseModel):
    stats: MapStats
    type: str
    mode: str
    name: te.Annotated[str, Field(alias="label")]
    img_small: UrlOrEmpty
    img_regular: UrlOrEmpty


class PlayerStats(BaseModel):
    id: te.Annotated[FaceitID, Field(alias="player_id")]
    game_id: GameID
    lifetime: LifetimeStats
    maps: te.Annotated[t.List[MapSegment], Field(alias="segments")]

    # TODO: Преобразование списка карт в словарь по "label"
    # Возможно лучше `GenericContainer` где атрибуты будут автоматически
    # генерироваться (есть карты, чьи названия не могут быть переменными)
