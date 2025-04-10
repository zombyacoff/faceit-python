from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from faceit._types import Annotated, UrlOrEmpty
from faceit.constants import GameID, Region

from .custom_types import (
    FaceitID,
    FaceitMatchID,
    LangFormattedAnyHttpUrl,
    ResponseContainer,
)


class GameInfo(BaseModel):
    region: str
    game_player_id: str
    level: Annotated[int, Field(alias="skill_level")]
    elo: Annotated[int, Field(alias="faceit_elo")]
    game_player_name: str
    # I think this attribute is outdated
    # level_label: str = Field(alias="skill_level_label")
    regions: ResponseContainer = ResponseContainer({})
    game_profile_id: str  # I have absolutely no idea what it is :<


class Player(BaseModel):
    id: Annotated[FaceitID, Field(alias="player_id")]
    nickname: str
    avatar: UrlOrEmpty
    country: str
    cover_image: UrlOrEmpty
    platforms: Optional[ResponseContainer[str]]
    games: ResponseContainer[GameInfo]
    settings: ResponseContainer
    friends_ids: List[FaceitID]
    new_steam_id: str
    steam_id_64: str
    steam_nickname: str
    memberships: List[str]
    faceit_url: LangFormattedAnyHttpUrl
    membership_type: str
    cover_featured_image: str
    infractions: ResponseContainer
    verified: bool
    activated_at: datetime


class BaseMatchPlayerStats(BaseModel):
    pass


# Не работает для игроков, игравших последний раз в ~авг. 2024 года
# Необходимо добавить значения по умолчанию для всех полей, которые могут отсутствовать
class CS2MatchPlayerStats(BaseMatchPlayerStats):
    game_mode: Annotated[str, Field(alias="Game Mode")]
    region: Annotated[str, Field(alias="Region")]
    kd_ratio: Annotated[float, Field(alias="K/D Ratio")]
    winner: Annotated[FaceitID, Field(alias="Winner")]
    player_id: Annotated[FaceitID, Field(alias="Player Id")]
    first_half_score: Annotated[int, Field(alias="First Half Score")]
    triple_kills: Annotated[int, Field(alias="Triple Kills")]
    assists: Annotated[int, Field(alias="Assists")]
    final_score: Annotated[int, Field(alias="Final Score")]
    penta_kills: Annotated[int, Field(alias="Penta Kills")]
    match_finished_at: Annotated[int, Field(alias="Match Finished At")]
    map: Annotated[str, Field(alias="Map")]
    overtime_score: Annotated[int, Field(alias="Overtime score")]
    deaths: Annotated[int, Field(alias="Deaths")]
    game: Annotated[str, Field(alias="Game")]
    nickname: Annotated[str, Field(alias="Nickname")]
    updated_at: Annotated[datetime, Field(alias="Updated At")]
    second_half_score: Annotated[int, Field(alias="Second Half Score")]
    team: Annotated[str, Field(alias="Team")]
    mvps: Annotated[int, Field(alias="MVPs")]
    match_id: Annotated[FaceitMatchID, Field(alias="Match Id")]
    headshots: Annotated[int, Field(alias="Headshots")]
    kills: Annotated[int, Field(alias="Kills")]
    result: Annotated[int, Field(alias="Result")]
    rounds: Annotated[int, Field(alias="Rounds")]
    match_round: Annotated[int, Field(alias="Match Round")]
    created_at: Annotated[datetime, Field(alias="Created At")]
    best_of: Annotated[int, Field(alias="Best Of")]
    adr: Annotated[float, Field(0, alias="ADR")]
    headshots_percentage: Annotated[float, Field(alias="Headshots %")]
    competition_id: Annotated[FaceitID, Field(alias="Competition Id")]
    score: Annotated[str, Field(alias="Score")]
    quadro_kills: Annotated[int, Field(alias="Quadro Kills")]
    kr_ratio: Annotated[float, Field(alias="K/R Ratio")]
    double_kills: Annotated[int, Field(0, alias="Double Kills")]


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
    cover_image: Optional[str] = None
    game: GameID
    type: Annotated[str, Field(alias="team_type")]
    members: Optional[List[str]] = None  # maybe List[Player] ?
    leader_id: Annotated[FaceitID, Field(alias="leader")]
    chat_room_id: str  # To be honest, I'm not totally sure what the ID is
    faceit_url: LangFormattedAnyHttpUrl


class Tournament(BaseModel):
    id: Annotated[FaceitID, Field(alias="tournament_id")]
    name: str
    featured_image: UrlOrEmpty  # maybe just str
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
    whitelist_countries: List[str]
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
    total_1v1_wins: Annotated[str, Field(alias="Total 1v1 Wins")]
    win_rate: Annotated[str, Field(alias="Win Rate %")]
    total_sniper_kills: Annotated[str, Field(alias="Total Sniper Kills")]
    longest_win_streak: Annotated[str, Field(alias="Longest Win Streak")]
    flash_success_rate: Annotated[str, Field(alias="Flash Success Rate")]
    total_flash_count: Annotated[str, Field(alias="Total Flash Count")]
    utility_success_rate: Annotated[str, Field(alias="Utility Success Rate")]
    total_damage: Annotated[str, Field(alias="Total Damage")]
    total_1v2_count: Annotated[str, Field(alias="Total 1v2 Count")]
    average_kd_ratio: Annotated[str, Field(alias="Average K/D Ratio")]
    wins: str
    sniper_kill_rate: Annotated[str, Field(alias="Sniper Kill Rate")]
    total_rounds_with_extended_stats: Annotated[
        str, Field(alias="Total Rounds with extended stats")
    ]
    kd_ratio: Annotated[str, Field(alias="K/D Ratio")]
    utility_damage_success_rate: Annotated[
        str, Field(alias="Utility Damage Success Rate")
    ]
    total_entry_count: Annotated[str, Field(alias="Total Entry Count")]
    average_headshots_percentage: Annotated[
        str, Field(alias="Average Headshots %")
    ]
    total_utility_successes: Annotated[
        str, Field(alias="Total Utility Successes")
    ]
    v2_win_rate: Annotated[str, Field(alias="1v2 Win Rate")]
    total_kills_with_extended_stats: Annotated[
        str, Field(alias="Total Kills with extended stats")
    ]
    matches: str
    entry_success_rate: Annotated[str, Field(alias="Entry Success Rate")]
    total_utility_damage: Annotated[str, Field(alias="Total Utility Damage")]
    total_entry_wins: Annotated[str, Field(alias="Total Entry Wins")]
    current_win_streak: Annotated[str, Field(alias="Current Win Streak")]
    utility_usage_per_round: Annotated[
        str, Field(alias="Utility Usage per Round")
    ]
    recent_results: Annotated[List[str], Field(alias="Recent Results")]
    total_1v1_count: Annotated[str, Field(alias="Total 1v1 Count")]
    total_headshots_percentage: Annotated[
        str, Field(alias="Total Headshots %")
    ]
    enemies_flashed_per_round: Annotated[
        str, Field(alias="Enemies Flashed per Round")
    ]
    flashes_per_round: Annotated[str, Field(alias="Flashes per Round")]
    sniper_kill_rate_per_round: Annotated[
        str, Field(alias="Sniper Kill Rate per Round")
    ]
    adr: Annotated[str, Field(alias="ADR")]
    v1_win_rate: Annotated[str, Field(alias="1v1 Win Rate")]
    total_utility_count: Annotated[str, Field(alias="Total Utility Count")]
    total_flash_successes: Annotated[str, Field(alias="Total Flash Successes")]
    total_1v2_wins: Annotated[str, Field(alias="Total 1v2 Wins")]
    total_matches: Annotated[str, Field(alias="Total Matches")]
    entry_rate: Annotated[str, Field(alias="Entry Rate")]
    total_enemies_flashed: Annotated[str, Field(alias="Total Enemies Flashed")]
    utility_damage_per_round: Annotated[
        str, Field(alias="Utility Damage per Round")
    ]


class MapStats(BaseModel):
    # TODO значения по умолчанию для полей "with_extended_stats" = None (или 0?),
    # так как они отсутсвтуют для старых матчей (предположу, что появились только в районе лета 2024)
    utility_success_rate: Annotated[float, Field(alias="Utility Success Rate")]
    entry_success_rate: Annotated[float, Field(alias="Entry Success Rate")]
    total_entry_wins: Annotated[int, Field(alias="Total Entry Wins")]
    # NOTE посмотреть матчи за 2023 ?
    total_rounds_with_extended_stats: Annotated[
        int, Field(alias="Total Rounds with extended stats")
    ]
    deaths: Annotated[int, Field(alias="Deaths")]
    # TODO преобразование в проценты (*100) таких полей, как "v2_win_rate", "v1_win_rate", ...
    v2_win_rate: Annotated[float, Field(alias="1v2 Win Rate")]
    total_kills_with_extended_stats: Annotated[
        int, Field(alias="Total Kills with extended stats")
    ]
    v1_win_rate: Annotated[float, Field(alias="1v1 Win Rate")]
    total_enemies_flashed: Annotated[int, Field(alias="Total Enemies Flashed")]
    mvps: Annotated[int, Field(alias="MVPs")]
    rounds: Annotated[int, Field(alias="Rounds")]
    average_assists: Annotated[float, Field(alias="Average Assists")]
    sniper_kill_rate: Annotated[float, Field(alias="Sniper Kill Rate")]

    # TODO корректную типизацию полей
    average_triple_kills: Annotated[str, Field(alias="Average Triple Kills")]
    average_quadro_kills: Annotated[str, Field(alias="Average Quadro Kills")]
    penta_kills: Annotated[str, Field(alias="Penta Kills")]
    total_flash_successes: Annotated[str, Field(alias="Total Flash Successes")]
    average_headshots_percentage: Annotated[
        str, Field(alias="Average Headshots %")
    ]
    average_kd_ratio: Annotated[str, Field(alias="Average K/D Ratio")]
    enemies_flashed_per_round: Annotated[
        str, Field(alias="Enemies Flashed per Round")
    ]
    total_flash_count: Annotated[str, Field(alias="Total Flash Count")]
    quadro_kills: Annotated[str, Field(alias="Quadro Kills")]
    flashes_per_round: Annotated[str, Field(alias="Flashes per Round")]
    total_headshots_percentage: Annotated[
        str, Field(alias="Total Headshots %")
    ]
    total_1v1_wins: Annotated[str, Field(alias="Total 1v1 Wins")]
    average_deaths: Annotated[str, Field(alias="Average Deaths")]
    kills: Annotated[str, Field(alias="Kills")]
    flash_success_rate: Annotated[str, Field(alias="Flash Success Rate")]
    entry_rate: Annotated[str, Field(alias="Entry Rate")]
    sniper_kill_rate_per_round: Annotated[
        str, Field(alias="Sniper Kill Rate per Round")
    ]
    average_penta_kills: Annotated[str, Field(alias="Average Penta Kills")]
    headshots_per_match: Annotated[str, Field(alias="Headshots per Match")]
    adr: Annotated[str, Field(alias="ADR")]
    total_damage: Annotated[str, Field(alias="Total Damage")]
    total_utility_count: Annotated[str, Field(alias="Total Utility Count")]
    total_entry_count: Annotated[str, Field(alias="Total Entry Count")]
    wins: Annotated[str, Field(alias="Wins")]
    total_sniper_kills: Annotated[str, Field(alias="Total Sniper Kills")]
    total_1v2_wins: Annotated[str, Field(alias="Total 1v2 Wins")]
    headshots: Annotated[str, Field(alias="Headshots")]
    total_1v2_count: Annotated[str, Field(alias="Total 1v2 Count")]
    utility_usage_per_round: Annotated[
        str, Field(alias="Utility Usage per Round")
    ]
    total_utility_damage: Annotated[str, Field(alias="Total Utility Damage")]
    kd_ratio: Annotated[str, Field(alias="K/D Ratio")]
    kr_ratio: Annotated[str, Field(alias="K/R Ratio")]
    average_kills: Annotated[str, Field(alias="Average Kills")]
    win_rate: Annotated[str, Field(alias="Win Rate %")]
    utility_damage_success_rate: Annotated[
        str, Field(alias="Utility Damage Success Rate")
    ]
    utility_damage_per_round: Annotated[
        str, Field(alias="Utility Damage per Round")
    ]
    total_utility_successes: Annotated[
        str, Field(alias="Total Utility Successes")
    ]
    matches: Annotated[str, Field(alias="Matches")]
    total_matches: Annotated[str, Field(alias="Total Matches")]
    average_mvps: Annotated[str, Field(alias="Average MVPs")]
    assists: Annotated[str, Field(alias="Assists")]
    total_1v1_count: Annotated[str, Field(alias="Total 1v1 Count")]
    triple_kills: Annotated[str, Field(alias="Triple Kills")]
    average_kr_ratio: Annotated[str, Field(alias="Average K/R Ratio")]


class MapSegment(BaseModel):
    stats: MapStats
    type: str
    mode: str
    name: Annotated[str, Field(alias="label")]
    img_small: UrlOrEmpty
    img_regular: UrlOrEmpty


class PlayerStats(BaseModel):
    id: Annotated[FaceitID, Field(alias="player_id")]
    game_id: GameID
    lifetime: LifetimeStats
    maps: Annotated[List[MapSegment], Field(alias="segments")]

    # TODO: Преобразование списка карт в словарь по "label"
    # Возможно лучше `GenericContainer` где атрибуты будут автоматически
    # генерироваться (есть карты, чьи названия не могут быть переменными)
