"""
Database seeder.

Creates one user per role for development / initial setup.

Run AFTER migrations have been applied:
    python -m alembic upgrade head
    python -m app.seed

Idempotent — existing users (matched by email) are left untouched.

Default credentials (change before any real deployment):
    admin@example.com      / Admin123        -> ADMIN
    drh@example.com        / Drh123          -> DRH
    directeur@example.com  / Directeur123    -> DIRECTEUR
    dg@example.com         / Dg123           -> DG
"""
from sqlalchemy import select

from app.core.enums import UserRole
from app.core.security import hash_password
from app.database import SessionLocal
from app.domains.users.model import User

SEED_USERS: list[dict] = [
    {
        "email": "admin@example.com",
        "full_name": "System Admin",
        "password": "Admin123",
        "role": UserRole.ADMIN,
    },
    {
        "email": "drh@example.com",
        "full_name": "Responsable RH",
        "password": "Drh123",
        "role": UserRole.DRH,
    },
    {
        "email": "directeur@example.com",
        "full_name": "Directeur Général Adjoint",
        "password": "Directeur123",
        "role": UserRole.DIRECTEUR,
    },
    {
        "email": "dg@example.com",
        "full_name": "Directeur Général",
        "password": "Dg123",
        "role": UserRole.DG,
    },
]


def seed() -> None:
    print("Seeding users...")
    created = skipped = 0

    db = SessionLocal()
    try:
        for data in SEED_USERS:
            existing = db.scalars(select(User).where(User.email == data["email"])).first()
            if existing:
                print(f"  [skip]    {data['email']} already exists")
                skipped += 1
                continue

            db.add(User(
                email=data["email"],
                full_name=data["full_name"],
                hashed_password=hash_password(data["password"]),
                role=data["role"],
            ))
            print(f"  [created] {data['email']}  ({data['role'].value})")
            created += 1

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"\nDone — {created} created, {skipped} skipped.")


if __name__ == "__main__":
    seed()