"""
Data access for tickets, including filtering, search and pagination
"""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session
from app.enums import Category, Priority, Status
from app.models import Ticket

SORTABLE_COLUMNS = {
    "createdAt": Ticket.created_at,
    "updatedAt": Ticket.updated_at,
    "priority": Ticket.priority,
    "status": Ticket.status,
    "title": Ticket.title,
}

class TicketRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def get(self, ticket_id: int) -> Ticket | None:
        return self.db.get(Ticket, ticket_id)

    def save(self, ticket: Ticket) -> Ticket:
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def _apply_filters(
        self,
        stmt: Select,
        *,
        status: Status | None,
        priority: Priority | None,
        category: Category | None,
        assigned_to: int | None,
        search: str | None,
    ) -> Select:
        if status is not None:
            stmt = stmt.where(Ticket.status == status)
        if priority is not None:
            stmt = stmt.where(Ticket.priority == priority)
        if category is not None:
            stmt = stmt.where(Ticket.category == category)
        if assigned_to is not None:
            stmt = stmt.where(Ticket.assigned_to_id == assigned_to)
        if search:
            # Lowering both sides makes the match explicitly case-insensitive
            # rather than relying on the collation of the underlying database.
            stmt = stmt.where(func.lower(Ticket.title).like(f"%{search.lower()}%"))
        return stmt

    def search(
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
        """Return one page of matching tickets plus the total match count."""
        filters = {
            "status": status,
            "priority": priority,
            "category": category,
            "assigned_to": assigned_to,
            "search": search,
        }

        total = self.db.scalar(
            self._apply_filters(select(func.count(Ticket.id)), **filters)
        ) or 0

        column = SORTABLE_COLUMNS.get(sort_by, Ticket.created_at)
        ordering = column.desc() if order == "desc" else column.asc()

        stmt = self._apply_filters(select(Ticket), **filters)
        stmt = stmt.order_by(ordering, Ticket.id.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        return list(self.db.scalars(stmt).unique()), total