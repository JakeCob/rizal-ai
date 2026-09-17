"""FastAPI dependencies: the verifier and the current user.

The current user dependency is the single place a request learns who the
learner is. It creates the users row on first sight, so anonymous sign-in
needs no separate registration call.
"""

import uuid
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.auth.jwt import InvalidTokenError, JwtVerifier, http_jwks_fetcher
from rizalai.config import get_settings
from rizalai.db.models import User
from rizalai.db.session import get_session
from rizalai.progress.rules import is_valid_timezone

bearer = HTTPBearer(auto_error=False)


@lru_cache
def get_verifier() -> JwtVerifier:
    settings = get_settings()
    fetcher = http_jwks_fetcher(settings.supabase_url) if settings.supabase_url else None
    return JwtVerifier(secret=settings.supabase_jwt_secret, jwks_fetcher=fetcher)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_or_create_user(session: AsyncSession, user_id: uuid.UUID) -> User:
    user = await session.get(User, user_id)
    if user is not None:
        return user
    await session.execute(insert(User).values(id=user_id).on_conflict_do_nothing(index_elements=["id"]))
    await session.commit()
    user = await session.get(User, user_id)
    assert user is not None
    return user


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    verifier: Annotated[JwtVerifier, Depends(get_verifier)],
    x_timezone: Annotated[str | None, Header()] = None,
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("missing bearer token")
    try:
        claims = verifier.verify(credentials.credentials)
    except InvalidTokenError as exc:
        raise _unauthorized("invalid token") from exc
    user = await get_or_create_user(session, claims.user_id)
    # The browser reports its IANA zone so streak days are local days (D17).
    if x_timezone and x_timezone != user.timezone and is_valid_timezone(x_timezone):
        user.timezone = x_timezone
        await session.commit()
    return user


CurrentUser = Annotated[User, Depends(current_user)]
