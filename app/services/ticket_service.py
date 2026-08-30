"""
Ticket business logic
"""
from sqlalchemy.orm import Session

from app.enums import Category, Priority, Role, Status, can_transition
from app.errors import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError
from app.models import Ticket, User
from app.repositories.ticket_repository import TicketRepository
from app.repositories.user_repository import UserRepository
from app.schemas import TicketCreate


class TicketService:
    def __init__(self, db: Session) -> None:
        self.tickets = TicketRepository(db)
        self.users = UserRepository(db)

    # ----- helpers -------------------------------------------------------

    def _get_ticket_or_404(self, ticket_id: int) -> Ticket:
        ticket = self.tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket {ticket_id} not found", code="TICKET_NOT_FOUND")
        return ticket

    @staticmethod
    def _require_agent(user: User, action: str) -> None:
        """Rule: agents own the ticket lifecycle; customers only report."""
        if user.role is not Role.AGENT:
            raise ForbiddenError(
                f"Only users with the AGENT role can {action}",
                code="AGENT_ROLE_REQUIRED",
            )

    # ----- commands ------------------------------------------------------

    def create_ticket(self, payload: TicketCreate, current_user: User) -> Ticket:
        ticket = Ticket(
            title=payload.title,
            description=payload.description,
            category=payload.category,
            priority=payload.priority,
            status=Status.OPEN,
            created_by_id=current_user.id,
        )
        return self.tickets.add(ticket)

    def get_ticket(self, ticket_id: int) -> Ticket:
        return self._get_ticket_or_404(ticket_id)

    def list_tickets(
        self,
        *,
        status: Status | None = None,
        priority: Priority | None = None,
        category: Category | None = None,
        assigned_to: int | None = None,
        search: str | None = None,
        sort_by: str = "createdAt",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Ticket], int]:
        return self.tickets.search(
            status=status,
            priority=priority,
            category=category,
            assigned_to=assigned_to,
            search=search,
            sort_by=sort_by,
            order=order,
            page=page,
            page_size=page_size,
        )

    def assign_ticket(self, ticket_id: int, assignee_id: int, current_user: User) -> Ticket:
        self._require_agent(current_user, "assign tickets")
        ticket = self._get_ticket_or_404(ticket_id)

        if ticket.status is Status.CLOSED:
            raise ConflictError(
                "A closed ticket cannot be reassigned", code="TICKET_CLOSED"
            )

        assignee = self.users.get(assignee_id)
        if assignee is None:
            raise NotFoundError(f"User {assignee_id} not found", code="USER_NOT_FOUND")

        # Business rule 3.
        if assignee.role is not Role.AGENT:
            raise BusinessRuleError(
                "Tickets can only be assigned to users with the AGENT role",
                code="ASSIGNEE_NOT_AGENT",
            )

        ticket.assigned_to_id = assignee.id
        return self.tickets.save(ticket)

    def change_status(self, ticket_id: int, target: Status, current_user: User) -> Ticket:
        """Single entry point for every status change, including closing.

        Both PATCH /status and PATCH /close route through here so the
        transition rules have exactly one implementation.
        """
        self._require_agent(current_user, "change ticket status")
        ticket = self._get_ticket_or_404(ticket_id)

        if ticket.status is target:
            raise ConflictError(
                f"Ticket is already {target.value}", code="NO_STATUS_CHANGE"
            )

        # Business rules 4 and 5.
        if not can_transition(ticket.status, target):
            raise ConflictError(
                f"Cannot transition from {ticket.status.value} to {target.value}",
                code="INVALID_STATUS_TRANSITION",
            )

        ticket.status = target
        return self.tickets.save(ticket)

    def close_ticket(self, ticket_id: int, current_user: User) -> Ticket:
        return self.change_status(ticket_id, Status.CLOSED, current_user)