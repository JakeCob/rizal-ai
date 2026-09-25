"""Behaviors for attempts, completion, hearts, streak, and the review seed
(SPEC.md 6.3, 6.5, 6.6). Every query is scoped to the current user."""

import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, select

from rizalai.content.loader import lesson_id
from rizalai.content.seed import seed_content
from rizalai.db.models import Exercise, ExerciseAttempt, ReviewQueue, User, UserProgress
from tests.helpers import mint_token

pytestmark = pytest.mark.anyio

CONTENT_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "content"
LESSON = lesson_id("scaffold-placeholder")


async def _seeded(db):
    await seed_content(db, CONTENT_DIR)
    rows = (
        await db.scalars(select(Exercise).where(Exercise.lesson_id == LESSON).order_by(Exercise.order_index))
    ).all()
    return rows


def _answer_for(row: Exercise, correct: bool) -> dict:
    if row.type == "comprehension_mc":
        right = int(row.answer["correct_index"])
        return {"optionIndex": right if correct else (right + 1) % len(row.payload["options"])}
    tokens = list(row.answer["answer_tokens"])
    return {"tokens": tokens if correct else tokens[:1]}


async def _post_attempt(client, token, row: Exercise, correct: bool, claim: bool | None = None):
    return await client.post(
        "/attempts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "exercise_id": str(row.id),
            "correct": correct if claim is None else claim,
            "response": _answer_for(row, correct),
            "duration_ms": 1200,
        },
    )


async def _complete(client, token, lesson=LESSON):
    return await client.post(f"/lessons/{lesson}/complete", headers={"Authorization": f"Bearer {token}"})


async def test_attempt_requires_auth_and_known_exercise(client, db):
    rows = await _seeded(db)
    response = await client.post(
        "/attempts", json={"exercise_id": str(rows[0].id), "correct": True, "response": {}, "duration_ms": 1}
    )
    assert response.status_code == 401
    _, token = mint_token()
    response = await client.post(
        "/attempts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "exercise_id": str(uuid.uuid4()),
            "correct": True,
            "response": {"tokens": ["x"]},
            "duration_ms": 1,
        },
    )
    assert response.status_code == 404


async def test_attempt_is_graded_server_side_and_spends_a_heart(client, db):
    rows = await _seeded(db)
    uid, token = mint_token()
    ok = await _post_attempt(client, token, rows[0], correct=True)
    assert ok.status_code == 202, ok.text
    assert ok.json() == {"correct": True, "hearts": 5}

    # The client claims correct, the response is wrong: server says wrong and spends a heart.
    lie = await _post_attempt(client, token, rows[0], correct=False, claim=True)
    assert lie.status_code == 202
    assert lie.json() == {"correct": False, "hearts": 4}

    stored = (await db.scalars(select(ExerciseAttempt).where(ExerciseAttempt.user_id == uid))).all()
    assert [a.correct for a in stored] == [True, False]
    assert all(a.lesson_id == LESSON for a in stored)


async def test_hearts_never_go_below_zero(client, db):
    rows = await _seeded(db)
    _, token = mint_token()
    for _ in range(7):
        response = await _post_attempt(client, token, rows[0], correct=False)
    assert response.json()["hearts"] == 0


async def test_complete_without_attempts_is_409(client, db):
    await _seeded(db)
    _, token = mint_token()
    response = await _complete(client, token)
    assert response.status_code == 409


async def test_complete_awards_xp_persists_progress_and_seeds_review(client, db):
    rows = await _seeded(db)
    uid, token = mint_token()
    for i, row in enumerate(rows):
        await _post_attempt(client, token, row, correct=(i != 2))  # one wrong
    response = await _complete(client, token)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["xp_earned"] == 50
    assert body["total_xp"] == 50
    assert body["streak_count"] == 1
    assert body["hearts"] == 4
    assert sorted(r["correct"] for r in body["results"]) == [False] + [True] * 5

    progress = await db.get(UserProgress, (uid, LESSON))
    assert progress is not None
    assert progress.completed_at is not None
    assert progress.xp_earned == 50
    assert float(progress.best_score) == pytest.approx(83.33, abs=0.01)
    assert progress.lesson_version

    queue = (await db.scalars(select(ReviewQueue).where(ReviewQueue.user_id == uid))).all()
    assert len(queue) == 6
    assert all(q.due_at > datetime.now(UTC) - timedelta(seconds=5) for q in queue)
    wrong = next(q for q in queue if q.exercise_id == rows[2].id)
    right = next(q for q in queue if q.exercise_id == rows[0].id)
    assert wrong.due_at < right.due_at  # a lapse comes back sooner

    user = await db.get(User, uid)
    assert user.total_xp == 50
    assert user.last_activity_date is not None


async def test_complete_uses_latest_attempt_per_exercise_and_re_grades(client, db):
    rows = await _seeded(db)
    _, token = mint_token()
    for row in rows:
        await _post_attempt(client, token, row, correct=False)
    for row in rows:
        await _post_attempt(client, token, row, correct=True, claim=False)  # claim is ignored
    body = (await _complete(client, token)).json()
    assert body["xp_earned"] == 60


async def test_listed_alternate_order_is_correct_and_completion_agrees(client, db):
    """D34: an order listed in accepted_orders grades correct on POST /attempts
    (no heart spent) and again when completion re-grades the latest attempt.
    Letter case is ignored on the way."""
    rows = await _seeded(db)
    ex5 = next(row for row in rows if row.payload["key"] == "ex5")
    _, token = mint_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post(
        "/attempts",
        headers=headers,
        json={
            "exercise_id": str(ex5.id),
            "correct": True,
            "response": {"tokens": ["Isang", "binata", "ang", "dumating"]},
            "duration_ms": 900,
        },
    )
    assert response.status_code == 202, response.text
    assert response.json() == {"correct": True, "hearts": 5}

    done = await _complete(client, token)
    assert done.status_code == 200, done.text
    results = {r["exercise_id"]: r["correct"] for r in done.json()["results"]}
    assert results[str(ex5.id)] is True
    assert done.json()["hearts"] == 5


async def test_streak_rules_over_days(client, db):
    rows = await _seeded(db)
    uid, token = mint_token()
    await _post_attempt(client, token, rows[0], correct=True)
    first = (await _complete(client, token)).json()
    assert first["streak_count"] == 1
    assert (await _complete(client, token)).status_code == 409  # nothing new since completion
    await _post_attempt(client, token, rows[0], correct=True)
    again = (await _complete(client, token)).json()
    assert again["streak_count"] == 1  # same day, unchanged

    user = await db.get(User, uid)
    user.last_activity_date = user.last_activity_date - timedelta(days=1)
    await db.commit()
    await _post_attempt(client, token, rows[0], correct=True)
    assert (await _complete(client, token)).json()["streak_count"] == 2

    user = await db.get(User, uid)
    user.last_activity_date = date.today() - timedelta(days=5)
    await db.commit()
    await _post_attempt(client, token, rows[0], correct=True)
    assert (await _complete(client, token)).json()["streak_count"] == 1


async def test_timezone_header_is_stored_and_used(client, db):
    uid, token = mint_token()
    response = await client.get(
        "/me", headers={"Authorization": f"Bearer {token}", "X-Timezone": "Asia/Manila"}
    )
    assert response.status_code == 200
    assert response.json()["timezone"] == "Asia/Manila"
    bad = await client.get("/me", headers={"Authorization": f"Bearer {token}", "X-Timezone": "Mars/Olympus"})
    assert bad.json()["timezone"] == "Asia/Manila"  # invalid header ignored


async def test_me_regenerates_hearts_on_read(client, db):
    uid, token = mint_token()
    await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    user = await db.get(User, uid)
    user.hearts = 3
    user.hearts_updated_at = datetime.now(UTC) - timedelta(hours=5)
    await db.commit()
    response = await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.json()["hearts"] == 4
    user = await db.get(User, uid)
    await db.refresh(user)
    assert user.hearts == 4


async def test_tree_marks_completed_lesson_done(client, db):
    rows = await _seeded(db)
    _, token = mint_token()
    await _post_attempt(client, token, rows[0], correct=True)
    await _complete(client, token)
    tree = (await client.get("/tree", headers={"Authorization": f"Bearer {token}"})).json()
    statuses = [lesson["status"] for lesson in tree["units"][0]["lessons"]]
    assert statuses[0] == "done"
    assert "active" not in statuses  # the remaining lessons are unpublished stubs


async def test_attempts_are_scoped_to_the_user(client, db):
    rows = await _seeded(db)
    _, token_a = mint_token()
    _, token_b = mint_token()
    await _post_attempt(client, token_a, rows[0], correct=True)
    response = await _complete(client, token_b)
    assert response.status_code == 409
    count = await db.scalar(select(func.count()).select_from(ExerciseAttempt))
    assert count == 1
