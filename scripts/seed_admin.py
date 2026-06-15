"""Seed a default ADMIN user (idempotent).

Credentials come from env: ADMIN_EMAIL / ADMIN_PASSWORD (sensible demo defaults).
Run after seed_data.py (needs the ADMIN role to exist):
    python3 scripts/seed_admin.py
"""
from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import src.db.models  # noqa: F401 — registers ORM models
from src.auth.password import hash_password
from src.db.engine import SessionLocal, create_tables
from src.db.models.user_models import RoleORM, UserORM

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@proppietario.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin1234!")


def seed_admin(verbose: bool = True) -> None:
    create_tables()
    db = SessionLocal()
    try:
        existing = db.query(UserORM).filter_by(email=ADMIN_EMAIL).first()
        if existing:
            if verbose:
                print(f"admin ya existe: {ADMIN_EMAIL}")
            return
        user = UserORM(
            id=str(uuid.uuid4()),
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            full_name="Administrador",
            is_active=True,
            email_verified=True,
        )
        db.add(user)
        db.flush()
        role = db.query(RoleORM).filter_by(name="ADMIN").first()
        if role:
            user.roles.append(role)
        db.commit()
        if verbose:
            print(f"admin creado: {ADMIN_EMAIL}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
