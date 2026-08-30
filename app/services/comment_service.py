"""Comment business logic."""
from sqlalchemy.orm import Session

from app.enums import Role, Status
from app.errors import ForbiddenError, NotFoundError
from app.models import Comment, User
from app.repositories.comment_repository import CommentRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas import CommentCreate


class CommentService:
    def __init__(self, db: Session) -> None:
        self.comments = CommentRepository(db)
        self.tickets = TicketRepository(db)

    def _get_ticket_or_404(self, ticket_id: int):
        ticket = self.tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket {ticket_id} not found", code="TICKET_NOT_FOUND")
        return ticket

    def add_comment(self, ticket_id: int, payload: CommentCreate, current_user: User) -> Comment:
        ticket = self._get_ticket_or_404(ticket_id)

        # A closed ticket is finished as far as the reporter is concerned;
        # agents may still annotate it for the record.
        if ticket.status is Status.CLOSED and current_user.role is not Role.AGENT:
            raise ForbiddenError(
                "Customers cannot comment on a closed ticket",
                code="TICKET_CLOSED",
            )

        comment = Comment(
            ticket_id=ticket.id,
            author_id=current_user.id,
            body=payload.body,
        )
        return self.comments.add(comment)

    def list_comments(self, ticket_id: int) -> list[Comment]:
        self._get_ticket_or_404(ticket_id)
        return self.comments.list_for_ticket(ticket_id)