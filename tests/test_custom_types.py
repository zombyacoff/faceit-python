import pytest
from pydantic import AnyHttpUrl, BaseModel, TypeAdapter, ValidationError

from faceit.models.custom_types import (
    FaceitID,
    FaceitMatchID,
    FaceitTeamID,
    LangFormattedAnyHttpUrl,
)
from faceit.models.custom_types.common import _LANG_PLACEHOLDER

langph = _LANG_PLACEHOLDER


@pytest.fixture(scope="session")
def lang_adapter() -> TypeAdapter[LangFormattedAnyHttpUrl]:
    return TypeAdapter(LangFormattedAnyHttpUrl)


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        (f"https://example.com/{langph}/docs", "https://example.com/docs"),
        (f"http://{langph}/foo/bar", "http://foo/bar"),
        (f"{langph}/foo/{langph}/bar", "foo/bar"),
        ("https://example.com/foo/bar", "https://example.com/foo/bar"),
        ("foo/bar", "foo/bar"),
        (f"foo/{langph}/bar", "foo/bar"),
        (f"foo/{langph}", "foo"),
        (f"{langph}/foo", "foo"),
        ("", ""),
    ],
)
def test_validate_success(
    input_value: str, expected: str, lang_adapter: TypeAdapter[LangFormattedAnyHttpUrl]
) -> None:
    if expected == "" or expected.startswith("http"):
        assert (
            input_value == expected
            if expected == ""
            else lang_adapter.validate_python(input_value) == AnyHttpUrl(expected)
        )
        return
    with pytest.raises(ValidationError):
        lang_adapter.validate_python(input_value)


class TestFaceitID:
    def test_valid_uuid(self, valid_uuid: str) -> None:
        faceit_id = FaceitID._validate(valid_uuid)
        assert isinstance(faceit_id, FaceitID)
        assert str(faceit_id) == valid_uuid

    def test_invalid_uuid(self) -> None:
        with pytest.raises(ValueError, match="Invalid FaceitID:"):
            FaceitID._validate("not-a-uuid")

        with pytest.raises(AttributeError):
            FaceitID(123)

    def test_suffix_handling(self, valid_uuid: str) -> None:
        suffixed_uuid = f"{valid_uuid}gui"

        with pytest.raises(ValueError, match="is not a valid UUID format"):
            FaceitID._validate(suffixed_uuid)

        if suffixed_uuid.endswith("gui"):
            cleaned_uuid = suffixed_uuid[:-3]
            faceit_id_from_cleaned = FaceitID._validate(cleaned_uuid)
            assert isinstance(faceit_id_from_cleaned, FaceitID)
            assert str(faceit_id_from_cleaned) == valid_uuid


class TestFaceitTeamID:
    def test_valid_team_id(self, valid_uuid: str) -> None:
        valid_team_id = f"team-{valid_uuid}"

        team_id = FaceitTeamID._validate(valid_team_id)
        assert isinstance(team_id, FaceitTeamID)
        assert str(team_id) == valid_team_id

    def test_missing_prefix(self, valid_uuid: str) -> None:
        with pytest.raises(ValueError, match="must start with 'team-'"):
            FaceitTeamID._validate(valid_uuid)

    def test_invalid_uuid_part(self) -> None:
        with pytest.raises(ValueError, match="contains invalid UUID part"):
            FaceitTeamID._validate("team-not-a-valid-uuid")

    def test_suffix_handling(self, valid_uuid: str) -> None:
        valid_team_id = f"team-{valid_uuid}"
        suffixed_team_id = f"{valid_team_id}gui"
        _ = FaceitTeamID._validate(valid_team_id)

        with pytest.raises(ValueError, match="contains invalid UUID part"):
            FaceitTeamID._validate(suffixed_team_id)

        if suffixed_team_id.endswith("gui"):
            cleaned_team_id = suffixed_team_id[:-3]
            team_id_from_cleaned = FaceitTeamID._validate(cleaned_team_id)
            assert isinstance(team_id_from_cleaned, FaceitTeamID)
            assert str(team_id_from_cleaned) == valid_team_id


class TestFaceitMatchID:
    def test_valid_match_id(self, valid_uuid: str) -> None:
        valid_match_id = f"1-{valid_uuid}"

        match_id = FaceitMatchID._validate(valid_match_id)
        assert isinstance(match_id, FaceitMatchID)
        assert str(match_id) == valid_match_id

    def test_missing_prefix(self, valid_uuid: str) -> None:
        with pytest.raises(ValueError, match="must start with '1-'"):
            FaceitMatchID._validate(valid_uuid)

    def test_invalid_uuid_part(self) -> None:
        with pytest.raises(ValueError, match="contains invalid UUID part"):
            FaceitMatchID._validate("1-not-a-valid-uuid")

    def test_suffix_handling(self, valid_uuid: str) -> None:
        valid_match_id = f"1-{valid_uuid}"
        suffixed_match_id = f"{valid_match_id}gui"
        _ = FaceitMatchID._validate(valid_match_id)

        with pytest.raises(ValueError, match="contains invalid UUID part"):
            FaceitMatchID._validate(suffixed_match_id)

        if suffixed_match_id.endswith("gui"):
            cleaned_match_id = suffixed_match_id[:-3]
            match_id_from_cleaned = FaceitMatchID._validate(cleaned_match_id)
            assert isinstance(match_id_from_cleaned, FaceitMatchID)
            assert str(match_id_from_cleaned) == valid_match_id


class TestPydanticIntegration:
    def test_faceit_id_in_model(self, valid_uuid: str) -> None:
        class UserModel(BaseModel):
            id: FaceitID

        user = UserModel(id=valid_uuid)
        assert isinstance(user.id, FaceitID)
        assert str(user.id) == valid_uuid

        suffixed_uuid = f"{valid_uuid}gui"
        user = UserModel(id=suffixed_uuid)
        assert isinstance(user.id, FaceitID)
        assert str(user.id) == valid_uuid

        with pytest.raises(ValidationError):
            UserModel(id="not-a-uuid")

    def test_faceit_team_id_in_model(self, valid_uuid: str) -> None:
        class TeamModel(BaseModel):
            id: FaceitTeamID

        valid_team_id = f"team-{valid_uuid}"
        team = TeamModel(id=valid_team_id)
        assert isinstance(team.id, FaceitTeamID)
        assert str(team.id) == valid_team_id

        suffixed_team_id = f"{valid_team_id}gui"
        team = TeamModel(id=suffixed_team_id)
        assert isinstance(team.id, FaceitTeamID)
        assert str(team.id) == valid_team_id

        with pytest.raises(ValidationError):
            TeamModel(id=valid_uuid)

        with pytest.raises(ValidationError):
            TeamModel(id="team-not-a-valid-uuid")

    def test_faceit_match_id_in_model(self, valid_uuid: str) -> None:
        class MatchModel(BaseModel):
            id: FaceitMatchID

        valid_match_id = f"1-{valid_uuid}"
        match = MatchModel(id=valid_match_id)
        assert isinstance(match.id, FaceitMatchID)
        assert str(match.id) == valid_match_id

        suffixed_match_id = f"{valid_match_id}gui"
        match = MatchModel(id=suffixed_match_id)
        assert isinstance(match.id, FaceitMatchID)
        assert str(match.id) == valid_match_id

        with pytest.raises(ValidationError):
            MatchModel(id=valid_uuid)

        with pytest.raises(ValidationError):
            MatchModel(id="1-not-a-valid-uuid")
