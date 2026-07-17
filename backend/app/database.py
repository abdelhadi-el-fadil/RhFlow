"""
Database engine + session factory + FastAPI dependency.

All other modules import ``get_db`` from here — never create sessions
directly so connection management stays in one place.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# create_engine is cheap to call once at module load.
# check_same_thread=False is only needed for SQLite (FastAPI uses threads).
_connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    _connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — yields one DB session per request.

    Commits on clean exit, rolls back on any exception, always closes.
    Use with ``Depends(get_db)`` in route signatures.
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
