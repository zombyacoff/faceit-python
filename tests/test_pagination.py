from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest
from pydantic import Field

from faceit.api.base import BaseResource
from faceit.api.pagination import (
    AsyncPageIterator,
    BasePageIterator,
    SyncPageIterator,
    TimestampPaginationConfig,
    check_pagination_support,
    pages,
)
from faceit.models import ItemPage
from faceit.models.custom_types import TimestampMs

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from faceit.types import RawAPIPageResponse


class _DummyResource(
    BaseResource[Any],
    resource_path="players",
):
    __slots__ = ("_items",)

    def __init__(self, items: list[dict[str, Any]]) -> None:
        super().__init__(client=None, raw=False)
        self._items = items

    def raw_method(
        self,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(2, ge=1, le=2),
    ) -> RawAPIPageResponse:
        items = self._items[offset : offset + limit]
        return {"items": items, "start": offset, "end": offset + limit}

    async def async_raw_method(
        self,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(2, ge=1, le=2),
    ) -> RawAPIPageResponse:
        return self.raw_method(offset=offset, limit=limit)

    def raw_method_with_unix(
        self,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(2, ge=1, le=2),
        start: int | None = None,  # noqa: ARG002
        to: int | None = None,
    ) -> RawAPIPageResponse:
        filtered = (
            self._items
            if to is None
            else [item for item in self._items if item["finished_at"] < to]
        )
        items = filtered[offset : offset + limit]
        return {"items": items, "start": offset, "end": offset + limit}

    async def async_raw_method_with_unix(
        self,
        *,
        offset: int = Field(0, ge=0),
        limit: int = Field(2, ge=1, le=2),
        start: int | None = None,
        to: int | None = None,
    ) -> RawAPIPageResponse:
        return self.raw_method_with_unix(offset=offset, limit=limit, start=start, to=to)


@dataclass(frozen=True)
class _ModelItem:
    id: int
    finished_at: int


@pytest.fixture
def raw_items() -> list[dict[str, Any]]:
    return [
        {"id": "a", "finished_at": 300},
        {"id": "b", "finished_at": 200},
        {"id": "c", "finished_at": 100},
    ]


@pytest.fixture
def dummy_resource(
    raw_items: list[dict[str, Any]],
) -> _DummyResource:
    return _DummyResource(raw_items)


@pytest.fixture
def raw_pages() -> tuple[RawAPIPageResponse, RawAPIPageResponse]:
    return (
        {"items": [{"id": "a"}, {"id": "b"}], "start": 0, "end": 2},
        {"items": [{"id": "b"}, {"id": "c"}], "start": 2, "end": 4},
    )


@pytest.fixture
def model_pages() -> tuple[ItemPage[dict[str, int]], ItemPage[dict[str, int]]]:
    return (
        ItemPage[dict[str, int]].model_validate({
            "items": [{"id": 1}, {"id": 2}],
            "start": 0,
            "end": 2,
        }),
        ItemPage[dict[str, int]].model_validate({
            "items": [{"id": 2}, {"id": 3}],
            "start": 2,
            "end": 4,
        }),
    )


def test_pages_rejects_one_or_less() -> None:
    with pytest.raises(ValueError):
        pages(1)


def test_validate_unix_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        BasePageIterator._validate_unix_config("invalid")
    with pytest.raises(ValueError):
        BasePageIterator._validate_unix_config({"key": "stats.finished_at"})


def test_check_pagination_support_for_non_resource_method_returns_false() -> None:
    def plain_method(limit: int = 2, offset: int = 0) -> RawAPIPageResponse:  # noqa: ARG001
        return {"items": [], "start": 0, "end": 0}

    assert check_pagination_support(plain_method) is False


def test_check_pagination_support_for_resource_method(
    dummy_resource: _DummyResource,
) -> None:
    pagination_limits = check_pagination_support(dummy_resource.raw_method)
    assert pagination_limits is not False
    assert pagination_limits.limit == 2
    assert pagination_limits.offset is None


def test_extract_unix_timestamp_from_raw_page() -> None:
    second_item_timestamp = 200
    page: RawAPIPageResponse = {
        "items": [
            {"stats": {"Match Finished At": 100}},
            {"stats": {"Match Finished At": second_item_timestamp}},
        ],
        "start": 0,
        "end": 2,
    }
    timestamp = BasePageIterator._extract_unix_timestamp(
        TimestampPaginationConfig(key="stats.Match Finished At", attr="finished_at"),
        page,
    )
    assert timestamp == second_item_timestamp


def test_extract_unix_timestamp_from_model_page() -> None:
    second_item_timestamp = 222
    page = ItemPage[_ModelItem].model_construct(
        items=(
            _ModelItem(id=1, finished_at=111),
            _ModelItem(id=2, finished_at=TimestampMs(second_item_timestamp)),
        ),
        offset=0,
        limit=2,
        time_from=None,
        time_to=None,
    )
    timestamp = BasePageIterator._extract_unix_timestamp(
        TimestampPaginationConfig(key="finished_at", attr="finished_at"), page
    )
    assert timestamp == second_item_timestamp


def test_sync_gather_from_iterator_raw_deduplicates(
    raw_pages: tuple[RawAPIPageResponse, RawAPIPageResponse],
) -> None:
    result = SyncPageIterator.gather_from_iterator(iter(raw_pages), deduplicate=True)
    assert result == [{"id": "a"}, {"id": "b"}, {"id": "c"}]


def test_sync_gather_from_iterator_model_merges_pages(
    model_pages: tuple[ItemPage[dict[str, int]], ItemPage[dict[str, int]]],
) -> None:
    result = SyncPageIterator.gather_from_iterator(
        iter(model_pages), "model", deduplicate=True
    )
    assert isinstance(result, ItemPage)
    assert tuple(result) == ({"id": 1}, {"id": 2}, {"id": 3})
    assert result.metadata is None


def test_sync_iterator_collects_using_bound_resource_method() -> None:
    resource = _DummyResource([{"id": 1}, {"id": 2}, {"id": 3}])
    iterator = SyncPageIterator(resource.raw_method, max_items=3)
    assert iterator.collect() == [{"id": 1}, {"id": 2}, {"id": 3}]


def test_sync_iterator_strips_user_pagination_params_with_warning(
    dummy_resource: _DummyResource,
) -> None:
    with pytest.warns(UserWarning):
        iterator = SyncPageIterator(
            dummy_resource.raw_method, max_items=2, offset=99, limit=99
        )
    assert iterator.current_offset == 0


def test_sync_unix_iterator_with_invalid_config_raises(
    dummy_resource: _DummyResource,
) -> None:
    with pytest.raises(ValueError):
        next(
            SyncPageIterator.unix(
                dummy_resource.raw_method,
                cfg={"key": "only-key"},
            )
        )


def test_sync_unix_iterator_yields_pages(dummy_resource: _DummyResource) -> None:
    iterator = SyncPageIterator.unix(
        dummy_resource.raw_method_with_unix,
        max_items=pages(2),
        cfg=TimestampPaginationConfig(key="finished_at", attr="finished_at"),
    )
    pages_result = list(iterator)
    assert len(pages_result) >= 1
    assert all("items" in page for page in pages_result)


def test_sync_iterator_collect_respects_safe_max_items(
    dummy_resource: _DummyResource,
) -> None:
    with patch.object(SyncPageIterator, "SAFE_MAX_PAGES", 1):
        iterator = SyncPageIterator(dummy_resource.raw_method, max_items="safe")
        result = iterator.collect(deduplicate=False)
    assert len(result) == 2


async def test_async_gather_from_iterator_raw() -> None:
    async def source() -> AsyncIterator[RawAPIPageResponse]:  # noqa: RUF029
        yield {"items": [{"id": 1}], "start": 0, "end": 1}
        yield {"items": [{"id": 2}], "start": 1, "end": 2}

    result = await AsyncPageIterator.gather_from_iterator(source(), deduplicate=True)
    assert result == [{"id": 1}, {"id": 2}]


async def test_async_unix_iterator_yields_pages(dummy_resource: _DummyResource) -> None:
    iterator = AsyncPageIterator.unix(
        dummy_resource.async_raw_method_with_unix,
        max_items=pages(2),
        cfg=TimestampPaginationConfig(key="finished_at", attr="finished_at"),
    )
    pages_result = [page async for page in iterator]
    assert len(pages_result) >= 1
    assert all("items" in page for page in pages_result)


async def test_async_unix_iterator_with_invalid_config_raises(
    dummy_resource: _DummyResource,
) -> None:
    with pytest.raises(ValueError):
        await anext(
            AsyncPageIterator.unix(
                dummy_resource.async_raw_method, cfg={"attr": "finished_at"}
            )
        )
