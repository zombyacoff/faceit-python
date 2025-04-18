import typing as t

from pydantic import BaseModel, Field, field_validator

from faceit._typing import Annotated, UrlOrEmpty
from faceit.constants import GameID

from ._custom_types import FaceitID, LangFormattedAnyHttpUrl

_RESULT_MAP: t.Final = {"faction1": "first", "faction2": "second"}


class PlayerSummary(BaseModel):
    id: Annotated[FaceitID, Field(alias="player_id")]
    nickname: str
    avatar: UrlOrEmpty
    level: Annotated[int, Field(alias="skill_level")]
    game_player_id: str
    game_player_name: str
    faceit_url: LangFormattedAnyHttpUrl


class Team(BaseModel):
    id: Annotated[
        t.Union[
            FaceitID,
            # The "bye" literal is used for placeholder teams in tournament
            # brackets when a team gets a free pass to the next round (no opponent)
            t.Literal["bye"],
        ],
        Field(alias="team_id"),
    ]
    name: Annotated[str, Field(alias="nickname")]
    avatar: UrlOrEmpty
    type: str
    players: t.List[PlayerSummary]


class Teams(BaseModel):
    first: Annotated[Team, Field(alias="faction1")]
    second: Annotated[Team, Field(alias="faction2")]


class Score(BaseModel):
    first: Annotated[int, Field(alias="faction1")]
    second: Annotated[int, Field(alias="faction2")]


class Results(BaseModel):
    winner: t.Literal["first", "second"]
    score: Score

    @field_validator("winner", mode="before")
    def convert_winner(cls, value: t.Any) -> str:  # noqa: N805
        if value in _RESULT_MAP:
            return _RESULT_MAP[value]
        raise ValueError(f"Invalid winner value: {value}")


class Match(BaseModel):
    id: Annotated[str, Field(alias="match_id")]
    game_id: GameID
    region: str
    type: Annotated[str, Field(alias="match_type")]
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
