from contextlib import suppress
from typing import Any

from faceit.constants import FACEIT_USERNAME_REGEX
from faceit.utils import create_uuid_validator

validate_player_id = create_uuid_validator(arg_name="player_id")


def validate_player_id_or_nickname(value: Any, /) -> str:
    with suppress(ValueError):
        return validate_player_id(value)
    if FACEIT_USERNAME_REGEX.fullmatch(value) is not None:
        return str(value)
    msg = f"Invalid identifier: {value!r} must be a valid UUID or FACEIT username."
    raise ValueError(msg)
