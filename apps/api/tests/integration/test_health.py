"""Behavior: given the API is running, when GET /health is called,
then 200 with status ok and db ok, and no auth is required."""

import pytest

pytestmark = pytest.mark.anyio


async def test_health_reports_ok_and_db_ok_without_auth(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}
