"""Behavior: the verifier accepts HS256 tokens signed with the project JWT
secret, and ES256 tokens whose key is published in the project's JWKS.
Both are Supabase configurations: legacy projects use the shared secret,
projects created since 2025 publish asymmetric keys."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from jwt.algorithms import ECAlgorithm

from rizalai.auth.jwt import InvalidTokenError, JwtVerifier
from tests.helpers import TEST_JWT_SECRET, mint_token


def test_hs256_token_yields_user_id():
    verifier = JwtVerifier(secret=TEST_JWT_SECRET)
    uid, token = mint_token()
    assert verifier.verify(token).user_id == uid


def test_hs256_token_with_wrong_audience_is_rejected():
    verifier = JwtVerifier(secret=TEST_JWT_SECRET)
    _, token = mint_token(audience="anon")
    with pytest.raises(InvalidTokenError):
        verifier.verify(token)


def test_es256_token_verified_against_jwks():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_jwk = ECAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    public_jwk["kid"] = "key-1"
    jwks = {"keys": [public_jwk]}

    uid = uuid.uuid4()
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(uid),
            "aud": "authenticated",
            "role": "authenticated",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        },
        private_key,
        algorithm="ES256",
        headers={"kid": "key-1"},
    )

    verifier = JwtVerifier(secret="", jwks_fetcher=lambda: jwks)
    assert verifier.verify(token).user_id == uid


def test_es256_token_with_unknown_kid_is_rejected():
    private_key = ec.generate_private_key(ec.SECP256R1())
    token = jwt.encode({"sub": str(uuid.uuid4()), "aud": "authenticated"}, private_key, algorithm="ES256")
    verifier = JwtVerifier(secret="", jwks_fetcher=lambda: {"keys": []})
    with pytest.raises(InvalidTokenError):
        verifier.verify(token)


def test_token_without_sub_is_rejected():
    now = datetime.now(UTC)
    token = jwt.encode(
        {"aud": "authenticated", "exp": int((now + timedelta(hours=1)).timestamp())},
        TEST_JWT_SECRET,
        algorithm="HS256",
    )
    verifier = JwtVerifier(secret=TEST_JWT_SECRET)
    with pytest.raises(InvalidTokenError):
        verifier.verify(token)
