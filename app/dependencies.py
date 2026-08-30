"""
Shared FastAPI dependencies
"""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import AppError, NotFoundError
from app.models import User
from app.repositories.user_repository import UserRepository

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> User:
    """Identify the caller from the X-User-Id header.

    This stands in for authentication, which the specification explicitly does
    not require. The header is parsed by hand rather than typed as `int` so a
    malformed value returns 400 with our standard error shape, instead of
    FastAPI's default 422 for a header type mismatch.
    """
    if x_user_id is None or not x_user_id.strip():
        raise AppError("X-User-Id header is required", code="MISSING_USER_HEADER")

    try:
        user_id = int(x_user_id)
    except ValueError:
        raise AppError("X-User-Id must be an integer", code="INVALID_USER_HEADER") from None

    user = UserRepository(db).get(user_id)
    if user is None:
        raise NotFoundError(f"User {user_id} not found", code="USER_NOT_FOUND")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]