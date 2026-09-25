"""Behaviors for the review queue (SPEC.md 6.6):
- GET /review/due returns up to 10 due items with their exercises, oldest
  due first, scoped to the user
- POST /review/answer reschedules through FSRS and reports the new state
- after 10 answered items in a practice session hearts refill to 5
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select

from rizalai.content.loader import lesson_id
from rizalai.content.seed import seed_content
from rizalai.db.models import Exercise, ReviewQueue, User
from rizalai.srs.scheduler import record_review
from tests.helpers import mint_token

pytestmark = pytest.mark.anyio

CONTENT_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "content"
LESSON = lesson_id("scaffold-placeholder")


async def _queue_all(db, uid, due_offset: timedelta):
    await seed_content(db, CONTENT_DIR)
    rows = (await db.scalars(select(Exercise).where(Exercise.lesson_id == LESSON))).all()
    now = datetime.now(UTC)
    for row in rows:
        item = await record_review(db, uid, row.id, correct=True, now=now)
        item.due_at = now + due_offset
    await db.commit()
    return rows


async def test_due_lists_only_due_items_for_this_user(client, db):
    uid, token = mint_token()
    await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    rows = await _queue_all(db, uid, timedelta(minutes=-1))
    other_uid, other_token = mint_token()
    await client.get("/me", headers={"Authorization": f"Bearer {other_token}"})

    response = await client.get("/review/due", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert len(items) == len(rows) == 6
    assert {i["exercise"]["exercise"]["type"] for i in items} <= {
        "sentence_assembly",
        "translate_line",
        "listen_tap",
        "comprehension_mc",
    }
    assert all(i["state"] == "learning" for i in items)

    none_due = await client.get("/review/due", headers={"Authorization": f"Bearer {other_token}"})
    assert none_due.json()["items"] == []


async def test_future_items_are_not_due(client, db):
    uid, token = mint_token()
    await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    await _queue_all(db, uid, timedelta(days=1))
    response = await client.get("/review/due", headers={"Authorization": f"Bearer {token}"})
    assert response.json()["items"] == []


async def test_answer_reschedules_and_refills_hearts_after_ten(client, db):
    uid, token = mint_token()
    await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    rows = await _queue_all(db, uid, timedelta(minutes=-1))
    user = await db.get(User, uid)
    user.hearts = 0
    await db.commit()

    headers = {"Authorization": f"Bearer {token}"}
    for n in range(10):
        row = rows[n % len(rows)]
        response = await client.post(
            "/review/answer",
            headers=headers,
            json={
                "exercise_id": str(row.id),
                "response": {"tokens": list(row.answer.get("answer_tokens", []))}
                if row.type != "comprehension_mc"
                else {"optionIndex": row.answer["correct_index"]},
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["correct"] is True
        assert body["session_answered"] == n + 1
    assert body["hearts"] == 5

    item = await db.scalar(
        select(ReviewQueue).where(ReviewQueue.user_id == uid, ReviewQueue.exercise_id == rows[0].id)
    )
    await db.refresh(item)
    assert item.reps >= 2
    assert item.due_at > datetime.now(UTC)


async def test_answer_accepts_a_listed_alternate_order(client, db):
    uid, token = mint_token()
    await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    rows = await _queue_all(db, uid, timedelta(minutes=-1))
    ex5 = next(row for row in rows if row.payload["key"] == "ex5")
    response = await client.post(
        "/review/answer",
        headers={"Authorization": f"Bearer {token}"},
        json={"exercise_id": str(ex5.id), "response": {"tokens": ["isang", "binata", "ang", "Dumating"]}},
    )
    assert response.status_code == 200, response.text
    assert response.json()["correct"] is True


async def test_answer_unknown_exercise_is_404(client, db):
    _, token = mint_token()
    response = await client.post(
        "/review/answer",
        headers={"Authorization": f"Bearer {token}"},
        json={"exercise_id": "00000000-0000-4000-8000-000000000000", "response": {"tokens": ["x"]}},
    )
    assert response.status_code == 404
