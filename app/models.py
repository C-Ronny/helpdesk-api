from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.config import COMMENT_MAX_LENGTH, DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH
from app.database import Base
from app.enums import Category, Priority, Role, Status

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[Role] = mapped_column(SAEnum(Role, native_enum=False))

class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH), index=True)
    description: Mapped[str] = mapped_column(String(DESCRIPTION_MAX_LENGTH))
    priority: Mapped[Priority] = mapped_column(
        SAEnum(Priority, native_enum=False), default=Priority.MEDIUM, index=True
    )
    status: Mapped[Status] = mapped_column(
        SAEnum(Status, native_enum=False), default=Status.OPEN, index=True
    )
    category: Mapped[Category] = mapped_column(SAEnum(Category, native_enum=False), index=True)

    # Authorship is derived from the X-User-Id header, never from the request
    # body, so a caller cannot file a ticket in someone else's name.
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_to_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_id], lazy="joined")
    assigned_to: Mapped[Optional["User"]] = relationship(
        foreign_keys=[assigned_to_id], lazy="joined"
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(String(COMMENT_MAX_LENGTH))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    ticket: Mapped["Ticket"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(lazy="joined")