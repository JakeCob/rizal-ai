"""Skill tree contract for GET /tree."""

import uuid
from typing import Literal

from pydantic import BaseModel

LessonStatus = Literal["locked", "active", "done"]


class TreeLesson(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    order_index: int
    status: LessonStatus
    xp_reward: int
    estimated_minutes: int


class TreeUnit(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    order_index: int
    lessons: list[TreeLesson]


class Tree(BaseModel):
    units: list[TreeUnit]
