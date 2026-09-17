"""Behaviors:
- Given no Authorization header, when an authed endpoint is called, then 401.
- Given an invalid or expired JWT, when an authed endpoint is called, then 401.
- Given a valid JWT for a user with no users row, when any authed endpoint is
  called, then a users row is created with hearts 5, xp 0, streak 0.
- Given a valid JWT, when the endpoint is called twice, then one users row exists.
"""

from datetime import timedelta

import pytest
from sqlalchemy import func, select

from rizalai.db.models import User
from tests.helpers import mint_token

pytestmark = pytest.mark.anyio


async def test_me_without_header_is_401(client):
    response = await client.get("/me")
    assert response.status_code == 401


async def test_me_with_garbage_token_is_401(client):
    response = await client.get("/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


async def test_me_with_wrong_secret_is_401(client):
    _, token = mint_token(secret="some-other-secret-that-is-at-least-32-bytes")
    response = await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


async def test_me_with_expired_token_is_401(client):
    _, token = mint_token(expires_in=timedelta(seconds=-10))
    response = await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


async def test_me_creates_user_with_defaults(client, db):
    uid, token = mint_token()
    response = await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(uid)
    assert body["hearts"] == 5
    assert body["total_xp"] == 0
    assert body["streak_count"] == 0

    row = await db.get(User, uid)
    assert row is not None
    assert row.hearts == 5


async def test_me_twice_creates_one_user(client, db):
    uid, token = mint_token()
    headers = {"Authorization": f"Bearer {token}"}
    await client.get("/me", headers=headers)
    await client.get("/me", headers=headers)
    count = await db.scalar(select(func.count()).select_from(User).where(User.id == uid))
    assert count == 1
