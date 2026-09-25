"""Behaviors:
- Given two units whose uuid5 ids sort opposite to their order_index, when
  GET /tree is called, then the active lesson is the first published lesson
  of the unit with the lowest order_index.
- Given a seeded unpublished stub, when GET /lessons/{id} or POST
  /lessons/{id}/complete is called for it, then 404, as for an unknown id,
  and no progress row is written.
- Given an unpublished lesson that has exercises, when POST /attempts or POST
  /review/answer names one of them, then 404 and no attempt or review row is
  written; and GET /review/due never lists one, even with a due queue row.
- Given a lesson the learner completed, when it is later unpublished, then
  GET /tree shows it locked (not done, not active) and GET /lessons/{id} is
  404, while the progress row and total_xp are untouched (D35).
"""

import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml
from sqlalchemy import func, select

from rizalai.content.loader import lesson_id, unit_id
from rizalai.content.seed import seed_content
from rizalai.contracts.tree import Tree
from rizalai.db.models import Exercise, ExerciseAttempt, Lesson, ReviewQueue, UserProgress
from tests.helpers import mint_token

pytestmark = pytest.mark.anyio

CONTENT_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "content"
STUB = lesson_id("noli-ch02-placeholder")
HIDDEN = lesson_id("hidden-lesson")
PUBLISHED = lesson_id("scaffold-placeholder")


async def _seed_with_copy(db, tmp_path, slug: str, *, published: bool, position: int | None = None) -> None:
    """Fixture content plus a copy of the scaffold lesson under a new slug,
    placed at `position` in the unit's lesson list (appended when None), so
    the extra lesson has real exercises in the database."""
    work = tmp_path / "content"
    shutil.copytree(CONTENT_DIR, work)
    unit_dir = work / "units" / "01-test-unit"
    lesson = yaml.safe_load((unit_dir / "01-scaffold-placeholder.yaml").read_text(encoding="utf-8"))
    lesson["slug"] = slug
    lesson["published"] = published
    (unit_dir / f"05-{slug}.yaml").write_text(yaml.safe_dump(lesson, allow_unicode=True), encoding="utf-8")
    unit = yaml.safe_load((unit_dir / "unit.yaml").read_text(encoding="utf-8"))
    lessons = unit["lessons"]
    lessons.insert(len(lessons) if position is None else position, f"05-{slug}.yaml")
    (unit_dir / "unit.yaml").write_text(yaml.safe_dump(unit), encoding="utf-8")
    await seed_content(db, work)


async def _seed_with_hidden_lesson(db, tmp_path) -> None:
    """Fixture content plus an unpublished copy of the scaffold lesson."""
    await _seed_with_copy(db, tmp_path, "hidden-lesson", published=False)


async def _first_exercise(db, lesson: object) -> Exercise:
    exercise = await db.scalar(
        select(Exercise).where(Exercise.lesson_id == lesson).order_by(Exercise.order_index)
    )
    assert exercise is not None, f"no exercise seeded for {lesson}"
    return exercise


async def _count(db, model, *where) -> int:
    return int(await db.scalar(select(func.count()).select_from(model).where(*where)) or 0)


def _slug_sorting_before(slug: str) -> str:
    """A unit slug whose uuid5 sorts before the given unit's, so ordering by
    unit id and ordering by order_index disagree."""
    target = str(unit_id(slug))
    for n in range(100):
        candidate = f"later-unit-{n}"
        if str(unit_id(candidate)) < target:
            return candidate
    raise AssertionError("no candidate slug sorts before the fixture unit")


async def test_tree_active_lesson_follows_unit_order_index(client, db, tmp_path):
    work = tmp_path / "content"
    shutil.copytree(CONTENT_DIR, work)
    later = _slug_sorting_before("test-unit")
    folder = work / "units" / "02-later-unit"
    folder.mkdir()
    (folder / "unit.yaml").write_text(
        f'slug: {later}\ntitle: "Later unit"\norder_index: 2\nlessons:\n  - 01-later.yaml\n',
        encoding="utf-8",
    )
    lesson = yaml.safe_load((work / "units" / "01-test-unit" / "01-scaffold-placeholder.yaml").read_text())
    lesson["slug"] = "later-lesson"
    (folder / "01-later.yaml").write_text(yaml.safe_dump(lesson, allow_unicode=True), encoding="utf-8")
    await seed_content(db, work)
    assert str(unit_id(later)) < str(unit_id("test-unit"))

    _, token = mint_token()
    response = await client.get("/tree", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    tree = Tree.model_validate(response.json())
    assert [u.slug for u in tree.units] == ["test-unit", later]
    active = [lesson.slug for unit in tree.units for lesson in unit.lessons if lesson.status == "active"]
    assert active == ["scaffold-placeholder"]
    assert tree.units[1].lessons[0].status == "locked"


async def test_get_unpublished_lesson_is_404(client, db):
    await seed_content(db, CONTENT_DIR)
    _, token = mint_token()
    response = await client.get(f"/lessons/{STUB}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


async def test_complete_unpublished_lesson_is_404(client, db, tmp_path):
    """The learner has an attempt on the hidden lesson, as if made while it
    was published. Without the published gate, completion would find that
    attempt, grade it, upsert a UserProgress row, and return 200; with no
    attempt at all it would return 409 and never reach the write, which is
    why the attempt is inserted here."""
    await _seed_with_hidden_lesson(db, tmp_path)
    exercise = await _first_exercise(db, HIDDEN)
    uid, token = mint_token()
    headers = {"Authorization": f"Bearer {token}"}
    await client.get("/me", headers=headers)
    db.add(
        ExerciseAttempt(
            user_id=uid,
            exercise_id=exercise.id,
            lesson_id=HIDDEN,
            correct=True,
            response={"tokens": ["x"]},
            duration_ms=1,
            created_at=datetime.now(UTC) - timedelta(minutes=1),
        )
    )
    await db.commit()

    response = await client.post(f"/lessons/{HIDDEN}/complete", headers=headers)
    assert response.status_code == 404
    assert await _count(db, UserProgress, UserProgress.lesson_id == HIDDEN) == 0


async def test_attempt_on_unpublished_exercise_is_404(client, db, tmp_path):
    await _seed_with_hidden_lesson(db, tmp_path)
    exercise = await _first_exercise(db, HIDDEN)
    _, token = mint_token()
    headers = {"Authorization": f"Bearer {token}"}
    hearts_before = (await client.get("/me", headers=headers)).json()["hearts"]
    response = await client.post(
        "/attempts",
        json={
            "exercise_id": str(exercise.id),
            "correct": True,
            "response": {"tokens": ["x"]},
            "duration_ms": 1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert await _count(db, ExerciseAttempt, ExerciseAttempt.exercise_id == exercise.id) == 0
    assert (await client.get("/me", headers=headers)).json()["hearts"] == hearts_before


async def test_review_answer_on_unpublished_exercise_is_404(client, db, tmp_path):
    await _seed_with_hidden_lesson(db, tmp_path)
    exercise = await _first_exercise(db, HIDDEN)
    _, token = mint_token()
    response = await client.post(
        "/review/answer",
        json={"exercise_id": str(exercise.id), "response": {"tokens": ["x"]}, "duration_ms": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert await _count(db, ReviewQueue, ReviewQueue.exercise_id == exercise.id) == 0
    assert await _count(db, ExerciseAttempt, ExerciseAttempt.exercise_id == exercise.id) == 0


async def test_review_due_skips_unpublished_exercises(client, db, tmp_path):
    await _seed_with_hidden_lesson(db, tmp_path)
    hidden = await _first_exercise(db, HIDDEN)
    visible = await _first_exercise(db, PUBLISHED)
    uid, token = mint_token()
    headers = {"Authorization": f"Bearer {token}"}
    await client.get("/me", headers=headers)
    past = datetime.now(UTC) - timedelta(minutes=5)
    for exercise in (hidden, visible):
        db.add(
            ReviewQueue(
                user_id=uid,
                exercise_id=exercise.id,
                due_at=past,
                stability=1.0,
                difficulty=5.0,
                state="review",
            )
        )
    await db.commit()

    response = await client.get("/review/due", headers=headers)
    assert response.status_code == 200, response.text
    listed = [item["exercise"]["id"] for item in response.json()["items"]]
    assert listed == [str(visible.id)], f"expected only {visible.id}, got {listed}"
    # Filtered at read time, not deleted: republishing the lesson brings the row back.
    kept = await db.scalar(
        select(ReviewQueue).where(ReviewQueue.user_id == uid, ReviewQueue.exercise_id == hidden.id)
    )
    assert kept is not None, "hidden review row was deleted"
    assert kept.due_at == past


async def test_tree_locks_done_lesson_once_unpublished(client, db, tmp_path):
    """A second published lesson follows the one that gets unpublished, so the
    test also sees that the done-then-unpublished lesson neither stays done
    nor takes the active slot: the next published lesson becomes active."""
    await _seed_with_copy(db, tmp_path, "next-lesson", published=True, position=1)
    exercise = await _first_exercise(db, PUBLISHED)
    uid, token = mint_token()
    headers = {"Authorization": f"Bearer {token}"}
    attempt = await client.post(
        "/attempts",
        headers=headers,
        json={
            "exercise_id": str(exercise.id),
            "correct": True,
            "response": {"tokens": list(exercise.answer["answer_tokens"])},
            "duration_ms": 1000,
        },
    )
    assert attempt.status_code == 202, attempt.text
    done = await client.post(f"/lessons/{PUBLISHED}/complete", headers=headers)
    assert done.status_code == 200, done.text
    xp_before = (await client.get("/me", headers=headers)).json()["total_xp"]

    lesson = await db.get(Lesson, PUBLISHED)
    assert lesson is not None
    lesson.published = False
    await db.commit()

    tree = Tree.model_validate((await client.get("/tree", headers=headers)).json())
    statuses = {node.slug: node.status for unit in tree.units for node in unit.lessons}
    assert statuses["scaffold-placeholder"] == "locked", statuses
    assert statuses["next-lesson"] == "active", statuses
    assert [slug for slug, status in statuses.items() if status == "active"] == ["next-lesson"], statuses
    assert (await client.get(f"/lessons/{PUBLISHED}", headers=headers)).status_code == 404
    assert (
        await _count(db, UserProgress, UserProgress.user_id == uid, UserProgress.lesson_id == PUBLISHED) == 1
    )
    assert (await client.get("/me", headers=headers)).json()["total_xp"] == xp_before
