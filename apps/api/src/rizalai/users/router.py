from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.auth.deps import CurrentUser
from rizalai.contracts.user import UserOut
from rizalai.db.session import get_session
from rizalai.progress.rules import apply_regen

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser, session: Annotated[AsyncSession, Depends(get_session)]) -> UserOut:
    if apply_regen(user):
        await session.commit()
    return UserOut.model_validate(user)
