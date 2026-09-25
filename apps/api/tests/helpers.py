"""Test helpers: minting session tokens shaped like the API's own (D33)."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt

TEST_JWT_SECRET = "test-secret-do-not-use-in-production"


def mint_token(
    user_id: uuid.UUID | None = None,
    *,
    secret: str = TEST_JWT_SECRET,
    expires_in: timedelta = timedelta(hours=1),
    audience: str = "authenticated",
) -> tuple[uuid.UUID, str]:
    uid = user_id or uuid.uuid4()
    now = datetime.now(UTC)
    claims = {
        "sub": str(uid),
        "aud": audience,
        "role": "authenticated",
        "is_anonymous": True,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_in).timestamp()),
    }
    return uid, jwt.encode(claims, secret, algorithm="HS256")
