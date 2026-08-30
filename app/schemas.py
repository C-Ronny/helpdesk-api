"""
Pydantic schemas: the shape of the data

Kept deliberately separate from the ORM models so the public API contract can
evolve independently of the database, and so internal columns are never
accidentally exposed.

Responses use the camelCase field names given in the specification; FastAPI
serialises by alias automatically.
"""
from datetime import datetime
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.config import COMMENT_MAX_LENGTH, DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH
from app.enums import Category, Priority, Role, Status

def _reject_blank(value: str) -> str:
    """Whitespace-only input is empty input."""
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be blank")
    return stripped

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: Role

class TicketCreate(BaseModel):
    title: str = Field(max_length=TITLE_MAX_LENGTH)
    description: str = Field(max_length=DESCRIPTION_MAX_LENGTH)
    category: Category
    priority: Priority = Priority.MEDIUM

    _strip_title = field_validator("title", "description")(_reject_blank)

class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    priority: Priority
    status: Status
    category: Category
    created_by: UserOut = Field(serialization_alias="createdBy")
    assigned_to: UserOut | None = Field(default=None, serialization_alias="assignedTo")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

class AssignRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    assignee_id: int = Field(alias="assigneeId")

class StatusUpdateRequest(BaseModel):
    status: Status

class CommentCreate(BaseModel):
    body: str = Field(max_length=COMMENT_MAX_LENGTH)

    _strip_body = field_validator("body")(_reject_blank)

class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int = Field(serialization_alias="ticketId")
    body: str
    author: UserOut
    created_at: datetime = Field(serialization_alias="createdAt")

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    """Envelope for paginated list responses."""

    items: list[T]
    total: int
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total_pages: int = Field(serialization_alias="totalPages")

class ErrorResponse(BaseModel):
    """The single error shape every failing endpoint returns."""

    detail: str
    code: str