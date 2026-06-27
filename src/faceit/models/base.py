from __future__ import annotations

from pydantic import BaseModel as _BaseModel, ConfigDict


class BaseModel(_BaseModel):
    model_config = ConfigDict(frozen=True)
