"""
Pydantic schemas — "auth" domain.
"""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Returned by POST /auth/login."""

    access_token: str
    token_type: str = "bearer"
