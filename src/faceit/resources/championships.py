# from __future__ import annotations

# from typing import Any, Dict, List, Literal, Optional, Union, overload

# from faceit._client import AsyncClient, SyncClient
# from faceit.models import Championship

# from .base import BaseResource


# class SyncChampionships(BaseResource[SyncClient]):
#     @overload
#     def get(self, game: str, *, raw_data: Literal[True], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: ...
#     @overload
#     def get(
#         self, game: str, *, raw_data: Literal[False] = False, params: Optional[Dict[str, Any]] = None
#     ) -> List[Championship]: ...
#     def get(
#         self, game: str, *, raw_data: bool = False, params: Optional[Dict[str, Any]] = None
#     ) -> Union[List[Championship], Dict[str, Any]]:
#         params = params or {}
#         result = self.client.request("GET", "/championships", {"game": game, **params})
#         return result if raw_data else [Championship.model_validate(ch) for ch in result["items"]]


# class AsyncChampionships(BaseResource[AsyncClient]):
#     @overload
#     async def get(
#         self, game: str, *, raw_data: Literal[True], params: Optional[Dict[str, Any]] = None
#     ) -> Dict[str, Any]: ...
#     @overload
#     async def get(
#         self, game: str, *, raw_data: Literal[False] = False, params: Optional[Dict[str, Any]] = None
#     ) -> List[Championship]: ...
#     async def get(
#         self, game: str, *, raw_data: bool = False, params: Optional[Dict[str, Any]] = None
#     ) -> Union[List[Championship], Dict[str, Any]]:
#         params = params or {}
#         result = await self.client.request("GET", "/championships", {"game": game, **params})
#         return result if raw_data else [Championship.model_validate(ch) for ch in result["items"]]
