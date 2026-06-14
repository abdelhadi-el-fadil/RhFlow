"""
Service — "auth" domain.

Holds all authentication business logic: credential checks, JWT issuing
and validation. The router only routes HTTP requests to these functions
and wraps the result.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    ExpiredSignatureError,
    InvalidTokenError,
    create_access_token,
    decode_token,
    verify_password,
)
from app.domains.auth.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    TokenExpiredException,
)
from app.domains.auth.schemas import TokenResponse
from app.domains.users.exceptions import UserNotFoundException
from app.domains.users.model import User


def login(db: Session, email: str, password: str) -> TokenResponse:
    """
    Verify credentials and return a JWT.

    The same error message is used whether the email is unknown or the
    password is wrong (account anti-enumeration).
    """
    # Exclude soft-deleted users from authentication lookups
    user = db.scalars(
        select(User).where(User.email == email, User.is_deleted == False)
    ).first()
    # Do not reveal whether the account exists, is disabled, or the password is wrong
    if user is None:
        raise InvalidCredentialsException()
    if not user.enabled or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsException()

    token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "email": user.email},
    )
    return TokenResponse(access_token=token)


def get_current_user_from_token(db: Session, token: str) -> User:
    """
    Decode the JWT, validate its content, and return the matching user.
    """
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise TokenExpiredException()
    except InvalidTokenError:
        raise InvalidTokenException()

    user_id = payload.get("sub")
    if user_id is None:
        raise InvalidTokenException()

    # Use a select to honour soft-delete and only return active rows
    user = db.scalars(
        select(User).where(User.id == int(user_id), User.is_deleted == False)
    ).first()
    if user is None:
        raise UserNotFoundException()

    # Disabled accounts should not be considered valid tokens
    if not user.enabled:
        raise InvalidTokenException()

    return user