import typing
from uuid import UUID

from faceit.constants import FACEIT_USERNAME_REGEX
from faceit.utils import create_uuid_validator, is_valid_uuid

validate_player_id = create_uuid_validator("player_id")


def validate_player_id_or_nickname(value: typing.Any, /) -> str:
    if isinstance(value, (UUID, bytes)) or is_valid_uuid(value):
        return validate_player_id(value)
    if FACEIT_USERNAME_REGEX.fullmatch(value) is not None:
        return str(value)
    raise ValueError(
        f"Invalid identifier: {value!r} must be a valid UUID or Faceit username."
    )
