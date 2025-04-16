from __future__ import annotations

import typing as t
from abc import ABC

from pydantic import validate_call

from faceit._typing import (
    APIResponseFormatT,
    ClientT,
    Model,
    ModelNotImplemented,
    Raw,
    RawAPIItem,
)
from faceit.http import AsyncClient, SyncClient
from faceit.models.custom_types import FaceitMatchID  # noqa: TCH001

from ._base import BaseResource, FaceitResourcePath


class BaseMatches(
    BaseResource[ClientT],
    ABC,
    resource_path=FaceitResourcePath.MATCHES,
):
    __slots__ = ()


class SyncMatches(BaseMatches[SyncClient], t.Generic[APIResponseFormatT]):
    __slots__ = ()

    @t.overload
    def details(
        self: SyncMatches[Raw], match_id: FaceitMatchID
    ) -> RawAPIItem: ...

    @t.overload
    def details(
        self: SyncMatches[Model], match_id: FaceitMatchID
    ) -> ModelNotImplemented: ...

    @validate_call
    def details(
        self, match_id: FaceitMatchID
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(self.PATH / str(match_id), expect_item=True),
            None,
        )

    @t.overload
    def stats(
        self: SyncMatches[Raw], match_id: FaceitMatchID
    ) -> RawAPIItem: ...

    @t.overload
    def stats(
        self: SyncMatches[Model], match_id: FaceitMatchID
    ) -> ModelNotImplemented: ...

    @validate_call
    def stats(
        self, match_id: FaceitMatchID
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            self._client.get(
                self.PATH / str(match_id) / "stats", expect_item=True
            ),
            None,
        )


class AsyncMatches(BaseMatches[AsyncClient], t.Generic[APIResponseFormatT]):
    __slots__ = ()

    @t.overload
    async def details(
        self: AsyncMatches[Raw], match_id: FaceitMatchID
    ) -> RawAPIItem: ...

    @t.overload
    async def details(
        self: AsyncMatches[Model], match_id: FaceitMatchID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def details(
        self, match_id: FaceitMatchID
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(match_id), expect_item=True
            ),
            None,
        )

    @t.overload
    async def stats(
        self: AsyncMatches[Raw], match_id: FaceitMatchID
    ) -> RawAPIItem: ...

    @t.overload
    async def stats(
        self: AsyncMatches[Model], match_id: FaceitMatchID
    ) -> ModelNotImplemented: ...

    @validate_call
    async def stats(
        self, match_id: FaceitMatchID
    ) -> t.Union[RawAPIItem, ModelNotImplemented]:
        return self._validate_response(
            await self._client.get(
                self.PATH / str(match_id) / "stats", expect_item=True
            ),
            None,
        )
