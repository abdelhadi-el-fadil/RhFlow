"""
Schémas Pydantic — domaine "auth".
"""
from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Retourné par POST /auth/login."""

    access_token: str
    token_type: str = "bearer"