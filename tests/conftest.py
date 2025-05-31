from uuid import uuid4

import pytest


@pytest.fixture
def valid_uuid() -> str:
    return str(uuid4())
