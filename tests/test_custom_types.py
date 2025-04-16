"""NOTE TO DEVELOPERS:

These tests were generated with the assistance of AI and may require
additional review or adjustments. Please verify that all test cases
properly cover the expected behavior of the custom types, especially
regarding edge cases and integration with `Pydantic`.
"""

import uuid
import pytest
from pydantic import BaseModel, ValidationError

from faceit.models.custom_types._faceit_uuid import (
    FaceitID,
    FaceitTeamID,
    FaceitMatchID,
)


@pytest.fixture
def valid_api_key():
    """Generate a valid UUID for API key tests."""
    return str(uuid.uuid4())


class TestFaceitID:
    def test_valid_uuid(self, valid_api_key):
        # Test with a valid UUID string
        valid_uuid = valid_api_key
        faceit_id = FaceitID.validate(valid_uuid)
        assert isinstance(faceit_id, FaceitID)
        assert str(faceit_id) == valid_uuid

    def test_invalid_uuid(self):
        # Test with an invalid UUID string
        with pytest.raises(ValueError, match="Invalid FaceitID:"):
            FaceitID.validate("not-a-uuid")

        # Test with a non-string, non-UUID value
        with pytest.raises(AttributeError):
            FaceitID(123)

    def test_suffix_handling(self, valid_api_key):
        # Test that the 'gui' suffix is NOT automatically handled
        # We need to manually remove it before validation
        valid_uuid = valid_api_key
        suffixed_uuid = f"{valid_uuid}gui"

        # This should work
        faceit_id = FaceitID.validate(valid_uuid)

        # This should fail because the suffix makes it an invalid UUID
        with pytest.raises(ValueError, match="is not a valid UUID format"):
            FaceitID.validate(suffixed_uuid)

        # Manual handling of suffix
        if suffixed_uuid.endswith("gui"):
            cleaned_uuid = suffixed_uuid[:-3]
            faceit_id_from_cleaned = FaceitID.validate(cleaned_uuid)
            assert isinstance(faceit_id_from_cleaned, FaceitID)
            assert str(faceit_id_from_cleaned) == valid_uuid


class TestFaceitTeamID:
    def test_valid_team_id(self, valid_api_key):
        # Test with a valid team ID (prefix + UUID)
        valid_uuid = valid_api_key
        valid_team_id = f"team-{valid_uuid}"

        team_id = FaceitTeamID.validate(valid_team_id)
        assert isinstance(team_id, FaceitTeamID)
        assert str(team_id) == valid_team_id

    def test_missing_prefix(self, valid_api_key):
        # Test with a UUID without the required prefix
        valid_uuid = valid_api_key

        with pytest.raises(ValueError, match="must start with 'team-'"):
            FaceitTeamID.validate(valid_uuid)

    def test_invalid_uuid_part(self):
        # Test with an invalid UUID part
        with pytest.raises(ValueError, match="contains invalid UUID part"):
            FaceitTeamID.validate("team-not-a-valid-uuid")

    def test_suffix_handling(self, valid_api_key):
        # Test that the 'gui' suffix is NOT automatically handled
        valid_uuid = valid_api_key
        valid_team_id = f"team-{valid_uuid}"
        suffixed_team_id = f"{valid_team_id}gui"

        # This should work
        team_id = FaceitTeamID.validate(valid_team_id)

        # This should fail because the suffix makes the UUID part invalid
        with pytest.raises(ValueError, match="contains invalid UUID part"):
            FaceitTeamID.validate(suffixed_team_id)

        # Manual handling of suffix
        if suffixed_team_id.endswith("gui"):
            cleaned_team_id = suffixed_team_id[:-3]
            team_id_from_cleaned = FaceitTeamID.validate(cleaned_team_id)
            assert isinstance(team_id_from_cleaned, FaceitTeamID)
            assert str(team_id_from_cleaned) == valid_team_id


class TestFaceitMatchID:
    def test_valid_match_id(self, valid_api_key):
        # Test with a valid match ID (prefix + UUID)
        valid_uuid = valid_api_key
        valid_match_id = f"1-{valid_uuid}"

        match_id = FaceitMatchID.validate(valid_match_id)
        assert isinstance(match_id, FaceitMatchID)
        assert str(match_id) == valid_match_id

    def test_missing_prefix(self, valid_api_key):
        # Test with a UUID without the required prefix
        valid_uuid = valid_api_key

        with pytest.raises(ValueError, match="must start with '1-'"):
            FaceitMatchID.validate(valid_uuid)

    def test_invalid_uuid_part(self):
        # Test with an invalid UUID part
        with pytest.raises(ValueError, match="contains invalid UUID part"):
            FaceitMatchID.validate("1-not-a-valid-uuid")

    def test_suffix_handling(self, valid_api_key):
        # Test that the 'gui' suffix is NOT automatically handled
        valid_uuid = valid_api_key
        valid_match_id = f"1-{valid_uuid}"
        suffixed_match_id = f"{valid_match_id}gui"

        # This should work
        match_id = FaceitMatchID.validate(valid_match_id)

        # This should fail because the suffix makes the UUID part invalid
        with pytest.raises(ValueError, match="contains invalid UUID part"):
            FaceitMatchID.validate(suffixed_match_id)

        # Manual handling of suffix
        if suffixed_match_id.endswith("gui"):
            cleaned_match_id = suffixed_match_id[:-3]
            match_id_from_cleaned = FaceitMatchID.validate(cleaned_match_id)
            assert isinstance(match_id_from_cleaned, FaceitMatchID)
            assert str(match_id_from_cleaned) == valid_match_id


# Test Pydantic integration
class TestPydanticIntegration:
    def test_faceit_id_in_model(self, valid_api_key):
        class UserModel(BaseModel):
            id: FaceitID

        # Valid UUID
        valid_uuid = valid_api_key
        user = UserModel(id=valid_uuid)
        assert isinstance(user.id, FaceitID)
        assert str(user.id) == valid_uuid

        # UUID with suffix - Pydantic automatically handles this
        suffixed_uuid = f"{valid_uuid}gui"
        user = UserModel(id=suffixed_uuid)
        assert isinstance(user.id, FaceitID)
        # The suffix should be automatically removed
        assert str(user.id) == valid_uuid

        # Invalid UUID
        with pytest.raises(ValidationError):
            UserModel(id="not-a-uuid")

    def test_faceit_team_id_in_model(self, valid_api_key):
        class TeamModel(BaseModel):
            id: FaceitTeamID

        # Valid team ID
        valid_uuid = valid_api_key
        valid_team_id = f"team-{valid_uuid}"
        team = TeamModel(id=valid_team_id)
        assert isinstance(team.id, FaceitTeamID)
        assert str(team.id) == valid_team_id

        # Team ID with suffix - Pydantic automatically handles this
        suffixed_team_id = f"{valid_team_id}gui"
        team = TeamModel(id=suffixed_team_id)
        assert isinstance(team.id, FaceitTeamID)
        # The suffix should be automatically removed
        assert str(team.id) == valid_team_id

        # Missing prefix
        with pytest.raises(ValidationError):
            TeamModel(id=valid_uuid)

        # Invalid UUID part
        with pytest.raises(ValidationError):
            TeamModel(id="team-not-a-valid-uuid")

    def test_faceit_match_id_in_model(self, valid_api_key):
        class MatchModel(BaseModel):
            id: FaceitMatchID

        # Valid match ID
        valid_uuid = valid_api_key
        valid_match_id = f"1-{valid_uuid}"
        match = MatchModel(id=valid_match_id)
        assert isinstance(match.id, FaceitMatchID)
        assert str(match.id) == valid_match_id

        # Match ID with suffix - Pydantic automatically handles this
        suffixed_match_id = f"{valid_match_id}gui"
        match = MatchModel(id=suffixed_match_id)
        assert isinstance(match.id, FaceitMatchID)
        # The suffix should be automatically removed
        assert str(match.id) == valid_match_id

        # Missing prefix
        with pytest.raises(ValidationError):
            MatchModel(id=valid_uuid)

        # Invalid UUID part
        with pytest.raises(ValidationError):
            MatchModel(id="1-not-a-valid-uuid")
