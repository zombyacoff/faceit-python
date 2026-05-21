import pytest
from pydantic import AnyHttpUrl, BaseModel, TypeAdapter, ValidationError

from faceit.models.custom_types import (
    FaceitID,
    FaceitMatchID,
    FaceitTeamID,
    LangFormattedAnyHttpUrl,
)
from faceit.models.custom_types.common import _LANG_PLACEHOLDER


@pytest.fixture(scope="module")
def lang_adapter() -> TypeAdapter[LangFormattedAnyHttpUrl]:
    return TypeAdapter(LangFormattedAnyHttpUrl)


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        (f"https://example.com/{_LANG_PLACEHOLDER}/docs", "https://example.com/docs"),
        (f"http://{_LANG_PLACEHOLDER}/foo/bar", "http://foo/bar"),
        (f"{_LANG_PLACEHOLDER}/foo/{_LANG_PLACEHOLDER}/bar", "foo/bar"),
        ("https://example.com/foo/bar", "https://example.com/foo/bar"),
        ("foo/bar", "foo/bar"),
        (f"foo/{_LANG_PLACEHOLDER}/bar", "foo/bar"),
        (f"foo/{_LANG_PLACEHOLDER}", "foo"),
        (f"{_LANG_PLACEHOLDER}/foo", "foo"),
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
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.ta = TypeAdapter(FaceitID)

    def test_valid_uuid(self, valid_uuid: str) -> None:
        faceit_id = self.ta.validate_python(valid_uuid)
        assert isinstance(faceit_id, FaceitID)
        assert str(faceit_id) == valid_uuid

    def test_invalid_uuid(self) -> None:
        with pytest.raises(ValidationError):
            self.ta.validate_python("not-a-uuid")

    def test_suffix_handling(self, valid_uuid: str) -> None:
        suffixed_uuid = f"{valid_uuid}gui"
        faceit_id = self.ta.validate_python(suffixed_uuid)
        assert isinstance(faceit_id, FaceitID)
        assert str(faceit_id) == valid_uuid


class TestFaceitTeamID:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.ta = TypeAdapter(FaceitTeamID)

    def test_valid_team_id(self, valid_uuid: str) -> None:
        valid_team_id = f"team-{valid_uuid}"
        team_id = self.ta.validate_python(valid_team_id)
        assert isinstance(team_id, FaceitTeamID)
        assert str(team_id) == valid_team_id

    def test_missing_prefix(self, valid_uuid: str) -> None:
        with pytest.raises(ValidationError):
            self.ta.validate_python(valid_uuid)

    def test_invalid_uuid_part(self) -> None:
        with pytest.raises(ValidationError):
            self.ta.validate_python("team-not-a-valid-uuid")

    def test_suffix_handling(self, valid_uuid: str) -> None:
        self.ta.validate_python(v := f"team-{valid_uuid}")
        self.ta.validate_python(f"{v}gui")


class TestFaceitMatchID:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.ta = TypeAdapter(FaceitMatchID)

    def test_valid_match_id(self, valid_uuid: str) -> None:
        valid_match_id = f"1-{valid_uuid}"
        match_id = self.ta.validate_python(valid_match_id)
        assert isinstance(match_id, FaceitMatchID)
        assert str(match_id) == valid_match_id

    def test_missing_prefix(self, valid_uuid: str) -> None:
        with pytest.raises(ValidationError):
            self.ta.validate_python(valid_uuid)

    def test_invalid_uuid_part(self) -> None:
        with pytest.raises(ValidationError):
            self.ta.validate_python("1-not-a-valid-uuid")

    def test_suffix_handling(self, valid_uuid: str) -> None:
        self.ta.validate_python(m := f"1-{valid_uuid}")
        self.ta.validate_python(f"{m}gui")


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

        with pytest.raises(ValidationError):
            MatchModel(id=valid_uuid)

        with pytest.raises(ValidationError):
            MatchModel(id="1-not-a-valid-uuid")
