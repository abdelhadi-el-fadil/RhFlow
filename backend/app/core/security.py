"""
Security utilities: password hashing (bcrypt via passlib) + JWT (PyJWT).

Why these two libraries?
- passlib  : high-level wrapper around bcrypt; handles salting automatically.
- PyJWT    : lightweight, no hidden magic — encode/decode are explicit calls.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.config import settings

# ---------------------------------------------------------------------------
# Password hashing — bcrypt
# ---------------------------------------------------------------------------
# bcrypt is deliberately slow (configurable "rounds") to resist brute-force.
# passlib manages the salt automatically; the hash string encodes it.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return the bcrypt hash of *plain*. Store this, never the plain text."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Re-hash *plain* with the salt from *hashed* and compare. Constant-time."""
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT — PyJWT
# ---------------------------------------------------------------------------
def create_access_token(
    subject: str | int,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Build and sign a JWT.

    Standard claims:
      sub  — subject (user id as string — JWT spec requires string)
      iat  — issued-at  (UTC timestamp)
      exp  — expiry     (UTC timestamp)

    Extra claims (e.g. {"role": "ADMIN", "email": "..."}) are merged in so
    downstream code can read role from the token without a DB round-trip.
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {"sub": str(subject), "iat": now, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)

    # jwt.encode() signs with SECRET_KEY (settings.ALGORITHM) and returns a string
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Verify signature + expiry, return the payload.

    Raises:
        jwt.ExpiredSignatureError : token is past its exp claim.
        jwt.InvalidTokenError     : signature mismatch, malformed, etc.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])