"""Behaviors for API-issued anonymous sessions (DECISIONS.md D33):
- a token carries a fresh user id, is_anonymous, the app issuer and
  audience, and an expiry a year out
- the existing verifier accepts it with the session secret
- a token signed with another secret or past expiry is rejected
- issuing without a secret is a configuration error
"""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from rizalai.auth.jwt import InvalidTokenError, JwtVerifier
from rizalai.auth.session import SESSION_TTL, issue_anonymous_token

SECRET = "session-secret-that-is-long-enough-for-hs256"


def test_issued_token_verifies_and_carries_claims():
    issued = issue_anonymous_token(SECRET)
    claims = JwtVerifier(secret=SECRET).verify(issued.access_token)
    assert claims.user_id == issued.user_id
    assert claims.is_anonymous is True
    raw = jwt.decode(issued.access_token, SECRET, algorithms=["HS256"], audience="authenticated")
    assert raw["iss"] == "rizalai"
    assert raw["aud"] == "authenticated"
    assert abs((issued.expires_at - datetime.now(UTC)) - SESSION_TTL) < timedelta(seconds=5)
    assert raw["exp"] == int(issued.expires_at.timestamp())


def test_two_tokens_are_two_users():
    assert issue_anonymous_token(SECRET).user_id != issue_anonymous_token(SECRET).user_id


def test_explicit_user_id_is_honored():
    uid = uuid.uuid4()
    assert issue_anonymous_token(SECRET, user_id=uid).user_id == uid


def test_wrong_secret_and_expired_are_rejected():
    issued = issue_anonymous_token(SECRET)
    with pytest.raises(InvalidTokenError):
        JwtVerifier(secret="another-secret-that-is-also-long-enough").verify(issued.access_token)
    expired = issue_anonymous_token(SECRET, ttl=timedelta(seconds=-1))
    with pytest.raises(InvalidTokenError):
        JwtVerifier(secret=SECRET).verify(expired.access_token)


def test_empty_secret_is_a_configuration_error():
    with pytest.raises(ValueError, match="SESSION_JWT_SECRET"):
        issue_anonymous_token("")
