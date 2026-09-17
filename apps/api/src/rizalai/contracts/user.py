"""Learner profile contract for GET /me."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    timezone: str
    total_xp: int
    streak_count: int
    hearts: int
    last_activity_date: date | None
