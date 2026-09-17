"""API-issued anonymous sessions (DECISIONS.md D33).

The first visit gets a long-lived HS256 token signed with SESSION_JWT_SECRET.
The verifier in rizalai.auth.jwt already accepts this shape, and a future
identity provider plugs into its JWKS path without touching callers.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.auth.deps import get_or_create_user
from rizalai.config import get_settings
from rizalai.db.session import get_session
from rizalai.progress.rules import is_valid_timezone

ISSUER = "rizalai"
AUDIENCE = "authenticated"
SESSION_TTL = timedelta(days=365)


@dataclass(frozen=True)
class IssuedSession:
    access_token: str
    user_id: uuid.UUID
    expires_at: datetime


def issue_anonymous_token(
    secret: str, user_id: uuid.UUID | None = None, ttl: timedelta = SESSION_TTL
) -> IssuedSession:
    if not secret:
        raise ValueError("SESSION_JWT_SECRET is required to issue sessions")
    uid = user_id or uuid.uuid4()
    now = datetime.now(UTC)
    expires_at = (now + ttl).replace(microsecond=0)
    claims = {
        "sub": str(uid),
        "iss": ISSUER,
        "aud": AUDIENCE,
        "role": AUDIENCE,
        "is_anonymous": True,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return IssuedSession(
        access_token=jwt.encode(claims, secret, algorithm="HS256"), user_id=uid, expires_at=expires_at
    )


class SessionOut(BaseModel):
    access_token: str
    user_id: uuid.UUID
    expires_at: datetime


router = APIRouter(prefix="/session", tags=["session"])


@router.post("/anonymous", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_anonymous_session(
    session: Annotated[AsyncSession, Depends(get_session)],
    x_timezone: Annotated[str | None, Header()] = None,
) -> SessionOut:
    issued = issue_anonymous_token(get_settings().session_jwt_secret)
    user = await get_or_create_user(session, issued.user_id)
    if x_timezone and is_valid_timezone(x_timezone) and user.timezone != x_timezone:
        user.timezone = x_timezone
        await session.commit()
    return SessionOut(access_token=issued.access_token, user_id=issued.user_id, expires_at=issued.expires_at)
