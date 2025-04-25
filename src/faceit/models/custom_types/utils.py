import typing as t

from pydantic_core import core_schema


def build_validatable_string_type_schema(
    obj: t.Type[t.Any], validator: t.Optional[t.Callable[..., t.Any]] = None, /
) -> core_schema.CoreSchema:
    if validator is None:
        # If no explicit `validator` is provided,
        # try to use the object's validate method
        if not hasattr(obj, "validate"):
            raise ValueError(
                f"No validator provided and {obj.__name__} has no 'validate' "
                f"method. Either provide a validator function or implement a "
                f"'validate' method."
            )
        validator = obj.validate
    # fmt: off
    return core_schema.union_schema([
        core_schema.is_instance_schema(obj),
        core_schema.str_schema(max_length=0),
        core_schema.chain_schema([
            core_schema.str_schema(),
            core_schema.no_info_plain_validator_function(validator),
        ]),
    ])
    # fmt: on
