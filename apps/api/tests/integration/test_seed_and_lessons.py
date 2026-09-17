"""Behaviors:
- Given the content directory, when the seed runs twice, then units, lessons,
  and exercises exist once and lesson.version equals the content hash.
- Given a seeded lesson, when GET /lessons/{id} is called with a valid JWT,
  then 200 with a body that validates against LessonOut.
- Given no JWT, then 401. Given an unknown id, then 404.
- Given a valid JWT, when GET /tree is called, then the first published lesson
  is active and unpublished lessons are locked.
- Given exercises in the database, then payload rows do not contain the
  answer fields, and the API merges them back.
"""

import uuid
from pathlib import Path

import pytest
from sqlalchemy import func, select

from rizalai.content.loader import content_hash, lesson_id, load_content
from rizalai.content.seed import seed_content
from rizalai.contracts.lesson import LessonOut
from rizalai.contracts.tree import Tree
from rizalai.db.models import Exercise, Lesson, Unit
from tests.helpers import mint_token

pytestmark = pytest.mark.anyio

CONTENT_DIR = Path(__file__).resolve().parents[3].parent / "content"


async def _counts(db) -> tuple[int, int, int]:
    units = await db.scalar(select(func.count()).select_from(Unit))
    lessons = await db.scalar(select(func.count()).select_from(Lesson))
    exercises = await db.scalar(select(func.count()).select_from(Exercise))
    return units, lessons, exercises


async def test_seed_is_idempotent_and_versions_by_hash(db):
    report = await seed_content(db, CONTENT_DIR)
    assert (report.units, report.lessons, report.exercises) == (1, 4, 6)
    first = await _counts(db)
    await seed_content(db, CONTENT_DIR)
    assert await _counts(db) == first == (1, 4, 6)

    units = load_content(CONTENT_DIR)
    placeholder = units[0].lessons[0]
    row = await db.get(Lesson, lesson_id(placeholder.slug))
    assert row is not None
    assert row.version == content_hash(placeholder)


async def test_exercise_payload_excludes_answer(db):
    await seed_content(db, CONTENT_DIR)
    rows = (await db.scalars(select(Exercise).order_by(Exercise.order_index))).all()
    assert len(rows) == 6
    for row in rows:
        assert "answer_tokens" not in row.payload
        assert "correct_index" not in row.payload
        assert row.answer  # never empty


async def test_get_lesson_requires_auth(client, db):
    await seed_content(db, CONTENT_DIR)
    response = await client.get(f"/lessons/{lesson_id('scaffold-placeholder')}")
    assert response.status_code == 401


async def test_get_lesson_returns_contract_shape(client, db):
    await seed_content(db, CONTENT_DIR)
    _, token = mint_token()
    response = await client.get(
        f"/lessons/{lesson_id('scaffold-placeholder')}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    lesson = LessonOut.model_validate(response.json())
    assert lesson.slug == "scaffold-placeholder"
    assert len(lesson.vignette) == 4
    assert len(lesson.exercises) == 6
    assert [e.order_index for e in lesson.exercises] == list(range(6))
    first = lesson.exercises[0].exercise
    assert first.type == "sentence_assembly"
    assert first.answer_tokens == ["Marami", "ang", "bisita", "ngayong", "gabi"]
    assert lesson.version == content_hash(load_content(CONTENT_DIR)[0].lessons[0])


async def test_get_unknown_lesson_is_404(client, db):
    _, token = mint_token()
    response = await client.get(f"/lessons/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


async def test_tree_marks_first_published_active_and_stubs_locked(client, db):
    await seed_content(db, CONTENT_DIR)
    _, token = mint_token()
    response = await client.get("/tree", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    tree = Tree.model_validate(response.json())
    assert len(tree.units) == 1
    statuses = [(lesson.slug, lesson.status) for lesson in tree.units[0].lessons]
    assert statuses == [
        ("scaffold-placeholder", "active"),
        ("noli-ch02-placeholder", "locked"),
        ("noli-ch03-placeholder", "locked"),
        ("noli-ch04-placeholder", "locked"),
    ]
    assert tree.units[0].lessons[0].xp_reward == 60
