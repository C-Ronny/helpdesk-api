"""
Read-only user endpoints
"""
from fastapi import APIRouter

from app.dependencies import DbSession
from app.errors import NotFoundError
from app.repositories.user_repository import UserRepository
from app.schemas import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut], summary="List all users")
def list_users(db: DbSession) -> list[UserOut]:
    return UserRepository(db).list_all()


@router.get("/{user_id}", response_model=UserOut, summary="Get a single user")
def get_user(user_id: int, db: DbSession) -> UserOut:
    user = UserRepository(db).get(user_id)
    if user is None:
        raise NotFoundError(f"User {user_id} not found", code="USER_NOT_FOUND")
    return user