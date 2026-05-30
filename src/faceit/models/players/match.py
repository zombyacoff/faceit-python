from __future__ import annotations

from abc import ABC
from datetime import datetime
from typing import Annotated, Any, Final, Literal, final

from pydantic import BaseModel, Field, field_validator

from faceit.constants import GameID
from faceit.models.custom_types import (
    FaceitID,
    FaceitMatchID,
    LangFormattedAnyHttpUrl,
    TimestampMs,
    TimestampSec,
)
from faceit.types import RegionIdentifier, UrlOrEmpty
from faceit.utils import StrEnum

from .general import MatchResult

_F1: Final = "faction1"
_F2: Final = "faction2"
_RESULT_MAP: Final = {
    _F1: "first",
    _F2: "second",
}


class Opponent(StrEnum):
    ABSENT = "bye"


@final
class PlayerSummary(BaseModel):
    id: Annotated[FaceitID, Field(alias="player_id")]
    nickname: str
    avatar: UrlOrEmpty
    level: Annotated[int, Field(alias="skill_level")]
    game_player_id: str
    game_player_name: str
    faceit_url: LangFormattedAnyHttpUrl


@final
class Team(BaseModel):
    id: Annotated[
        FaceitID | Opponent,
        Field(alias="team_id"),
    ]
    name: Annotated[str, Field(alias="nickname")]
    avatar: UrlOrEmpty
    type: str
    players: list[PlayerSummary]


@final
class Teams(BaseModel):
    first: Annotated[Team, Field(alias=_F1)]
    second: Annotated[Team, Field(alias=_F2)]


@final
class Score(BaseModel):
    first: Annotated[int, Field(alias=_F1)]
    second: Annotated[int, Field(alias=_F2)]


@final
class Results(BaseModel):
    winner: Literal["first", "second"]
    score: Score

    @field_validator("winner", mode="before")
    @classmethod
    def convert_winner(cls, value: Any) -> str:
        if value in _RESULT_MAP:
            return _RESULT_MAP[value]
        msg = f"Invalid winner value: {value}"
        raise ValueError(msg)


@final
class Match(BaseModel):
    id: Annotated[str, Field(alias="match_id")]
    game_id: GameID
    region: RegionIdentifier
    type: Annotated[str, Field(alias="match_type")]
    game_mode: str
    max_players: int
    teams_size: int
    teams: Teams
    playing_players: list[FaceitID]
    competition_id: FaceitID
    competition_name: str
    competition_type: str
    organizer_id: str
    status: str
    started_at: TimestampSec
    finished_at: TimestampSec
    results: Results
    faceit_url: LangFormattedAnyHttpUrl


class AbstractMatchPlayerStats(BaseModel, ABC):
    """
    Abstract class for player match statistics models in the inheritance hierarchy.

    Serves as a common type for various game-specific player statistics models.
    Useful for type annotations when the return type depends on the :attr:`~.game` parameter
    provided by the user, allowing different ``MatchPlayerStats`` subclasses to be
    returned based on the game context.
    """

    game: Annotated[GameID, Field(alias="Game")]


@final
# Doesn't work for players who last played around Aug 2024
# (when extended stats were added to the API)
# TODO: Need to add default values for all fields that may be missing
class CS2MatchPlayerStats(AbstractMatchPlayerStats):
    id: Annotated[FaceitMatchID, Field(alias="Match Id")]
    game_mode: Annotated[str, Field(alias="Game Mode")]
    region: Annotated[RegionIdentifier, Field(alias="Region")]
    kd_ratio: Annotated[float, Field(alias="K/D Ratio")]
    winner: Annotated[FaceitID | None, Field(None, alias="Winner")]
    player_id: Annotated[FaceitID, Field(alias="Player Id")]
    first_half_score: Annotated[int, Field(alias="First Half Score")]
    triple_kills: Annotated[int, Field(alias="Triple Kills")]
    assists: Annotated[int, Field(alias="Assists")]
    final_score: Annotated[int, Field(alias="Final Score")]
    penta_kills: Annotated[int, Field(alias="Penta Kills")]
    finished_at: Annotated[TimestampMs, Field(alias="Match Finished At")]
    map: Annotated[str, Field(alias="Map")]
    overtime_score: Annotated[int, Field(alias="Overtime score")]
    deaths: Annotated[int, Field(alias="Deaths")]
    nickname: Annotated[str, Field(alias="Nickname")]
    updated_at: Annotated[datetime, Field(alias="Updated At")]
    second_half_score: Annotated[int, Field(alias="Second Half Score")]
    team: Annotated[str, Field(alias="Team")]
    mvps: Annotated[int, Field(alias="MVPs")]
    headshots: Annotated[int, Field(alias="Headshots")]
    kills: Annotated[int, Field(alias="Kills")]
    result: Annotated[MatchResult, Field(alias="Result")]
    rounds: Annotated[int, Field(alias="Rounds")]
    match_round: Annotated[int, Field(alias="Match Round")]
    created_at: Annotated[datetime, Field(alias="Created At")]
    best_of: Annotated[int, Field(alias="Best Of")]
    adr: Annotated[float, Field(0.0, alias="ADR")]
    headshots_percentage: Annotated[float, Field(alias="Headshots %")]
    competition_id: Annotated[FaceitID, Field(alias="Competition Id")]
    score: Annotated[str, Field(alias="Score")]
    quadro_kills: Annotated[int, Field(alias="Quadro Kills")]
    kr_ratio: Annotated[float, Field(alias="K/R Ratio")]
    double_kills: Annotated[int, Field(0, alias="Double Kills")]
