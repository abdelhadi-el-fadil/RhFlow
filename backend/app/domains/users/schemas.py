"""
Pydantic schemas — "users" domain.
"""
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    gsm: str | None = None
    role: UserRole


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    full_name: str | None = None
    gsm: str | None = None
    role: UserRole | None = None
    enabled: bool | None = None


class UserResponse(BaseModel):
    """Public representation of a user (never hashed_password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None
    gsm: str | None
    signature_key: str | None
    signature_content_type: str | None
    role: UserRole
    enabled: bool


class UserSignatureResponse(BaseModel):
    signature_key: str
    signature_content_type: str
    url: str