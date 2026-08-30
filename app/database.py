"""
Database engine, session factory, and the per-request session dependency
"""


from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL


class Base(DeclarativeBase):
    """Parent class every ORM model inherits from."""


# check_same_thread is a SQLite-specific relaxation required because the web
# server may serve a request on a different thread than the one that opened
# the connection.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Yield a session per request and always close it, even on error."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()