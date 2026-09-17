"""Verify Supabase access tokens.

The API issues its own HS256 tokens (rizalai.auth.session). A future
identity provider publishes asymmetric keys at a JWKS URL. The verifier
supports both: an HS256 token is checked against the secret, an ES256 or
RS256 token is checked against the JWKS key whose kid matches the header.
"""

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from jwt import PyJWK

JwksFetcher = Callable[[], dict[str, Any]]

JWKS_TTL_SECONDS = 600
ASYMMETRIC_ALGS = ("ES256", "RS256")


class InvalidTokenError(Exception):
    """The token is missing, malformed, expired, or signed by an unknown key."""


@dataclass(frozen=True)
class TokenClaims:
    user_id: uuid.UUID
    is_anonymous: bool
    raw: dict[str, Any]


def http_jwks_fetcher(jwks_url: str) -> JwksFetcher:
    url = jwks_url

    def fetch() -> dict[str, Any]:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data

    return fetch


class JwtVerifier:
    def __init__(
        self,
        secret: str,
        jwks_fetcher: JwksFetcher | None = None,
        audience: str = "authenticated",
    ) -> None:
        self._secret = secret
        self._jwks_fetcher = jwks_fetcher
        self._audience = audience
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_fetched_at = 0.0

    def verify(self, token: str) -> TokenClaims:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise InvalidTokenError("malformed token") from exc

        alg = header.get("alg")
        if alg == "HS256":
            if not self._secret:
                raise InvalidTokenError("HS256 token but no JWT secret configured")
            key: Any = self._secret
        elif alg in ASYMMETRIC_ALGS:
            key = self._key_for_kid(header.get("kid"))
        else:
            raise InvalidTokenError(f"unsupported algorithm {alg!r}")

        try:
            claims = jwt.decode(token, key, algorithms=[alg], audience=self._audience)
        except jwt.PyJWTError as exc:
            raise InvalidTokenError(str(exc)) from exc

        sub = claims.get("sub")
        try:
            user_id = uuid.UUID(str(sub))
        except (ValueError, TypeError) as exc:
            raise InvalidTokenError("token has no usable sub claim") from exc

        return TokenClaims(user_id=user_id, is_anonymous=bool(claims.get("is_anonymous", False)), raw=claims)

    def _key_for_kid(self, kid: str | None) -> Any:
        if self._jwks_fetcher is None:
            raise InvalidTokenError("asymmetric token but no JWKS source configured")
        jwk = self._find_key(kid)
        if jwk is None:
            self._jwks_cache = None  # key rotation: refetch once
            jwk = self._find_key(kid)
        if jwk is None:
            raise InvalidTokenError(f"no JWKS key with kid {kid!r}")
        return PyJWK.from_dict(jwk).key

    def _find_key(self, kid: str | None) -> dict[str, Any] | None:
        jwks = self._jwks()
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                return dict(jwk)
        return None

    def _jwks(self) -> dict[str, Any]:
        assert self._jwks_fetcher is not None
        now = time.monotonic()
        if self._jwks_cache is None or now - self._jwks_fetched_at > JWKS_TTL_SECONDS:
            self._jwks_cache = self._jwks_fetcher()
            self._jwks_fetched_at = now
        return self._jwks_cache
