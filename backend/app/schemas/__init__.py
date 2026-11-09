from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer


def _as_utc_iso(value: datetime) -> str:
    # SQLite drops tzinfo. Everything we store is UTC, so say so on the way out.
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


UtcDatetime = Annotated[datetime, PlainSerializer(_as_utc_iso, return_type=str)]


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page[T](ApiModel):
    items: list[T]
    total: int
    limit: int
    offset: int
