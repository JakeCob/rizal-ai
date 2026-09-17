import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.auth.deps import CurrentUser
from rizalai.contracts.reflection import ReflectionOut
from rizalai.db.models import Lesson
from rizalai.db.session import get_session
from rizalai.generation.llm import LLMClient, get_llm_client
from rizalai.generation.service import get_or_generate_reflection

router = APIRouter(tags=["reflection"])


@router.get("/lessons/{lesson_id}/reflection", response_model=ReflectionOut)
async def get_reflection(
    lesson_id: uuid.UUID,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
) -> ReflectionOut:
    lesson = await session.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="lesson not found")
    return await get_or_generate_reflection(session, lesson, llm)
