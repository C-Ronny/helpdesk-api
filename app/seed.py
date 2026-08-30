"""
Seed a small fixed set of users.

The specification defines no user-creation endpoint, so users are created at
startup. IDs are stable and documented in the README, which lets a reviewer
send requests immediately.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import Role
from app.models import User

SEED_USERS = [
    {"id": 1, "name": "Ama Mensah", "email": "ama@gmail.com", "role": Role.CUSTOMER},
    {"id": 2, "name": "Tobi Woode", "email": "tobi@gmail.com", "role": Role.CUSTOMER},
    {"id": 3, "name": "Efua Owusu", "email": "efua@ikieguy.com", "role": Role.AGENT},
    {"id": 4, "name": "Eric Asare", "email": "eric@ikieguy.com", "role": Role.AGENT},
]


def seed_users(db: Session) -> None:
    if db.scalar(select(User).limit(1)) is not None:
        return
    db.add_all(User(**data) for data in SEED_USERS)
    db.commit()