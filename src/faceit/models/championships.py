import typing

from pydantic import BaseModel

from faceit.constants import Region
from faceit.models.custom_types import (
    FaceitID,
    LangFormattedAnyHttpUrl,
    NullableList,
    ResponseContainer,
)
from faceit.types import UrlOrEmpty, UUIDOrEmpty


class JoinChecks(BaseModel):
    min_skill_level: int
    max_skill_level: int
    whitelist_geo_countries: typing.List[str]
    whitelist_geo_countries_min_players: int
    blacklist_geo_countries: typing.List[str]
    join_policy: str
    membership_type: str
    allowed_team_types: typing.List[str]


class SubstitutionConfiguration(BaseModel):
    max_substitutes: int
    max_substitutions: int


class Prize(BaseModel):
    rank: int
    faceit_points: int


class Stream(BaseModel):
    active: bool
    platform: str
    source: str
    title: str


class Championship(BaseModel):
    id: FaceitID
    # `championship_id: FaceitID` unnecessary
    name: str
    cover_image: UrlOrEmpty
    background_image: UrlOrEmpty
    avatar: UrlOrEmpty
    organizer_id: str
    description: str
    type: str
    status: str
    game_id: str
    region: Region
    featured: bool
    subscription_start: int
    checkin_start: int
    checkin_clear: int
    subscription_end: int
    championship_start: int
    slots: int
    current_subscriptions: int
    join_checks: JoinChecks
    anticheat_required: bool
    rules_id: UUIDOrEmpty
    substitution_configuration: SubstitutionConfiguration
    full: bool
    checkin_enabled: bool
    total_rounds: int
    schedule: ResponseContainer[typing.Any]
    total_groups: int
    subscriptions_locked: bool
    seeding_strategy: str
    faceit_url: LangFormattedAnyHttpUrl
    prizes: NullableList[Prize]
    total_prizes: int
    stream: Stream
