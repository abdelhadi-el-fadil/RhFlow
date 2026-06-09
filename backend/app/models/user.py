import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum
from app.models.base import Base

class UserRole(str, enum.Enum):
    ADMIN     = "ADMIN"
    DRH       = "DRH"
    DIRECTEUR = "DIRECTEUR"
    DG        = "DG"

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    full_name       = Column(String, nullable=True)
    gsm             = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role            = Column(Enum(UserRole, name="userrole"), default=UserRole.DRH, nullable=False)
    enabled         = Column(Boolean, default=True)