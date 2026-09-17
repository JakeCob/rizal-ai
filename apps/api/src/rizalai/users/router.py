import uuid
from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from rizalai.auth.deps import CurrentUser

router = APIRouter(tags=["users"])


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    timezone: str
    total_xp: int
    streak_count: int
    hearts: int
    last_activity_date: date | None


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
