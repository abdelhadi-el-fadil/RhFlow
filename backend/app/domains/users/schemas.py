"""
Schémas Pydantic — domaine "users".
"""
from pydantic import BaseModel, ConfigDict

from app.core.enums import UserRole


class UserResponse(BaseModel):
    """Représentation publique d'un utilisateur (jamais hashed_password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None
    gsm: str | None
    role: UserRole
    enabled: bool