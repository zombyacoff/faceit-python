import typing as t
from abc import ABC
from datetime import datetime

import typing_extensions as te
from pydantic import BaseModel, Field, field_validator

from faceit.constants import GameID, Region
from faceit.models.custom_types import (
    FaceitID,
    FaceitMatchID,
    LangFormattedAnyHttpUrl,
)
from faceit.types import UrlOrEmpty

_NoOpponent: te.TypeAlias = t.Literal["bye"]

_RESULT_MAP: t.Final = {"faction1": "first", "faction2": "second"}


class PlayerSummary(BaseModel):
    id: te.Annotated[FaceitID, Field(alias="player_id")]
    nickname: str
    avatar: UrlOrEmpty
    level: te.Annotated[int, Field(alias="skill_level")]
    game_player_id: str
    game_player_name: str
    faceit_url: LangFormattedAnyHttpUrl


class Team(BaseModel):
    id: te.Annotated[t.Union[FaceitID, _NoOpponent], Field(alias="team_id")]
    name: te.Annotated[str, Field(alias="nickname")]
    avatar: UrlOrEmpty
    type: str
    players: t.List[PlayerSummary]


class Teams(BaseModel):
    first: te.Annotated[Team, Field(alias="faction1")]
    second: te.Annotated[Team, Field(alias="faction2")]


class Score(BaseModel):
    first: te.Annotated[int, Field(alias="faction1")]
    second: te.Annotated[int, Field(alias="faction2")]


class Results(BaseModel):
    winner: t.Literal["first", "second"]
    score: Score

    @field_validator("winner", mode="before")
    def convert_winner(cls, value: t.Any) -> str:
        if value in _RESULT_MAP:
            return _RESULT_MAP[value]
        raise ValueError(f"Invalid winner value: {value}")


class Match(BaseModel):
    id: te.Annotated[str, Field(alias="match_id")]
    game_id: GameID
    region: Region
    type: te.Annotated[str, Field(alias="match_type")]
    game_mode: str
    max_players: int
    teams_size: int
    teams: Teams
    playing_players: t.List[FaceitID]
    competition_id: FaceitID
    competition_name: str
    competition_type: str
    organizer_id: str
    status: str
    started_at: int
    finished_at: int
    results: Results
    faceit_url: LangFormattedAnyHttpUrl


class AbstractMatchPlayerStats(BaseModel, ABC):
    """Abstract class for player match statistics models in the inheritance hierarchy.

    Serves as a common type for various game-specific player statistics models.
    Useful for type annotations when the return type depends on the ``game`` parameter
    provided by the user, allowing different ``MatchPlayerStats`` subclasses to be
    returned based on the game context.
    """


# Не работает для игроков, игравших последний раз в ~авг. 2024 года
# Необходимо добавить значения по умолчанию для всех полей, которые могут отсутствовать
class CS2MatchPlayerStats(AbstractMatchPlayerStats):
    game_mode: te.Annotated[str, Field(alias="Game Mode")]
    region: te.Annotated[Region, Field(alias="Region")]
    kd_ratio: te.Annotated[float, Field(alias="K/D Ratio")]
    winner: te.Annotated[FaceitID, Field(alias="Winner")]
    player_id: te.Annotated[FaceitID, Field(alias="Player Id")]
    first_half_score: te.Annotated[int, Field(alias="First Half Score")]
    triple_kills: te.Annotated[int, Field(alias="Triple Kills")]
    assists: te.Annotated[int, Field(alias="Assists")]
    final_score: te.Annotated[int, Field(alias="Final Score")]
    penta_kills: te.Annotated[int, Field(alias="Penta Kills")]
    match_finished_at: te.Annotated[int, Field(alias="Match Finished At")]
    map: te.Annotated[str, Field(alias="Map")]
    overtime_score: te.Annotated[int, Field(alias="Overtime score")]
    deaths: te.Annotated[int, Field(alias="Deaths")]
    game: te.Annotated[str, Field(alias="Game")]
    nickname: te.Annotated[str, Field(alias="Nickname")]
    updated_at: te.Annotated[datetime, Field(alias="Updated At")]
    second_half_score: te.Annotated[int, Field(alias="Second Half Score")]
    team: te.Annotated[str, Field(alias="Team")]
    mvps: te.Annotated[int, Field(alias="MVPs")]
    match_id: te.Annotated[FaceitMatchID, Field(alias="Match Id")]
    headshots: te.Annotated[int, Field(alias="Headshots")]
    kills: te.Annotated[int, Field(alias="Kills")]
    result: te.Annotated[int, Field(alias="Result")]
    rounds: te.Annotated[int, Field(alias="Rounds")]
    match_round: te.Annotated[int, Field(alias="Match Round")]
    created_at: te.Annotated[datetime, Field(alias="Created At")]
    best_of: te.Annotated[int, Field(alias="Best Of")]
    adr: te.Annotated[float, Field(0, alias="ADR")]
    headshots_percentage: te.Annotated[float, Field(alias="Headshots %")]
    competition_id: te.Annotated[FaceitID, Field(alias="Competition Id")]
    score: te.Annotated[str, Field(alias="Score")]
    quadro_kills: te.Annotated[int, Field(alias="Quadro Kills")]
    kr_ratio: te.Annotated[float, Field(alias="K/R Ratio")]
    double_kills: te.Annotated[int, Field(0, alias="Double Kills")]
