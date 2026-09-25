import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.auth.deps import CurrentUser
from rizalai.contracts.reflection import ReflectionOut
from rizalai.db.session import get_session
from rizalai.generation.llm import LLMClient, get_llm_client
from rizalai.generation.service import get_or_generate_reflection
from rizalai.lessons.service import get_published_lesson

router = APIRouter(tags=["reflection"])


@router.get("/lessons/{lesson_id}/reflection", response_model=ReflectionOut)
async def get_reflection(
    lesson_id: uuid.UUID,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
) -> ReflectionOut:
    lesson = await get_published_lesson(session, lesson_id)
    return await get_or_generate_reflection(session, lesson, llm)
