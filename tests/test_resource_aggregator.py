from dataclasses import dataclass

import pytest

from faceit.resources.resource_aggregator import (
    BaseResources,
    resource_aggregator,
)


class DummyClient:
    pass


@dataclass(eq=False, frozen=True)
class DummyResource:
    client: DummyClient
    raw: bool = False


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
