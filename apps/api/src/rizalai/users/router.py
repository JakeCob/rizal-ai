from fastapi import APIRouter

from rizalai.auth.deps import CurrentUser
from rizalai.contracts.user import UserOut

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
