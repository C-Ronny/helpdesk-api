from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import User

class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def list_all(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.id)))