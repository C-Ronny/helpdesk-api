"""
Comment endpoints, nested under a ticket
"""

from fastapi import APIRouter, status as http_status

from app.dependencies import CurrentUser, DbSession
from app.schemas import CommentCreate, CommentOut
from app.services.comment_service import CommentService

router = APIRouter(prefix="/tickets/{ticket_id}/comments", tags=["comments"])


@router.post(
    "",
    response_model=CommentOut,
    status_code=http_status.HTTP_201_CREATED,
    summary="Add a comment to a ticket",
)
def add_comment(
    ticket_id: int, payload: CommentCreate, db: DbSession, current_user: CurrentUser
) -> CommentOut:
    return CommentService(db).add_comment(ticket_id, payload, current_user)


@router.get("", response_model=list[CommentOut], summary="List comments on a ticket")
def list_comments(ticket_id: int, db: DbSession, current_user: CurrentUser) -> list[CommentOut]:
    return CommentService(db).list_comments(ticket_id)