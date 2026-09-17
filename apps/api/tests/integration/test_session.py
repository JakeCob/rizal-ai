"""Behaviors for POST /session/anonymous (DECISIONS.md D33): the first tap
creates a learner with no form, the token works on every authed endpoint,
and each call is a new learner."""

import pytest

from rizalai.db.models import User

pytestmark = pytest.mark.anyio


async def test_anonymous_session_creates_a_user_and_works_on_me(client, db):
    response = await client.post("/session/anonymous")
    assert response.status_code == 201, response.text
    body = response.json()
    assert set(body) == {"access_token", "user_id", "expires_at"}

    me = await client.get("/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["id"] == body["user_id"]
    assert me.json()["hearts"] == 5

    import uuid

    row = await db.get(User, uuid.UUID(body["user_id"]))
    assert row is not None


async def test_each_call_is_a_new_learner(client, db):
    a = (await client.post("/session/anonymous")).json()["user_id"]
    b = (await client.post("/session/anonymous")).json()["user_id"]
    assert a != b


async def test_timezone_header_applies_at_session_creation(client, db):
    body = (await client.post("/session/anonymous", headers={"X-Timezone": "Asia/Manila"})).json()
    me = await client.get("/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.json()["timezone"] == "Asia/Manila"
