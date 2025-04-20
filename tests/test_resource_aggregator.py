import pytest
from faceit._resources._aggregator_factory import (
    resource_aggregator,
    BaseResources,
)


class DummyClient:
    pass


class DummyResource:
    def __init__(self, client: DummyClient, raw: bool = False):
        self.client = client
        self.raw = raw


@resource_aggregator
class ResourcesForTest(BaseResources):
    resource1: DummyResource
    raw_resource2: DummyResource


@pytest.fixture
def client() -> DummyClient:
    return DummyClient()


@pytest.fixture
def resources(client: DummyClient) -> ResourcesForTest:
    return ResourcesForTest(client)


def test_properties_created(resources: ResourcesForTest):
    assert hasattr(resources, "resource1")
    assert hasattr(resources, "raw_resource2")


def test_property_types(resources: ResourcesForTest):
    assert isinstance(resources.resource1, DummyResource)
    assert isinstance(resources.raw_resource2, DummyResource)


def test_property_raw_flag(resources: ResourcesForTest):
    assert resources.resource1.raw is False
    assert resources.raw_resource2.raw is True


def test_client_passed(resources: ResourcesForTest, client: DummyClient):
    assert resources.resource1.client is client
    assert resources.raw_resource2.client is client
