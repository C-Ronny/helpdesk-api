"""
Ticket endpoints
"""

from math import ceil
from typing import Annotated

from fastapi import APIRouter, Query, status as http_status

from app.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.dependencies import CurrentUser, DbSession
from app.enums import Category, Priority, Status
from app.repositories.ticket_repository import SORTABLE_COLUMNS
from app.schemas import (
    AssignRequest,
    Page,
    StatusUpdateRequest,
    TicketCreate,
    TicketOut,
)
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post(
    "",
    response_model=TicketOut,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create a ticket",
)
def create_ticket(payload: TicketCreate, db: DbSession, current_user: CurrentUser) -> TicketOut:
    return TicketService(db).create_ticket(payload, current_user)


@router.get("", response_model=Page[TicketOut], summary="List, filter and search tickets")
def list_tickets(
    db: DbSession,
    current_user: CurrentUser,
    status: Annotated[Status | None, Query(description="Filter by status")] = None,
    priority: Annotated[Priority | None, Query(description="Filter by priority")] = None,
    category: Annotated[Category | None, Query(description="Filter by category")] = None,
    assigned_to: Annotated[
        int | None, Query(alias="assignedTo", description="Filter by assigned agent id")
    ] = None,
    search: Annotated[
        str | None, Query(description="Case-insensitive partial match on title")
    ] = None,
    sort_by: Annotated[str, Query(alias="sortBy")] = "createdAt",
    order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> Page[TicketOut]:
    if sort_by not in SORTABLE_COLUMNS:
        sort_by = "createdAt"

    items, total = TicketService(db).list_tickets(
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
    return Page[TicketOut](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get("/{ticket_id}", response_model=TicketOut, summary="Get a ticket by id")
def get_ticket(ticket_id: int, db: DbSession, current_user: CurrentUser) -> TicketOut:
    return TicketService(db).get_ticket(ticket_id)


@router.patch("/{ticket_id}/assign", response_model=TicketOut, summary="Assign a ticket to an agent")
def assign_ticket(
    ticket_id: int, payload: AssignRequest, db: DbSession, current_user: CurrentUser
) -> TicketOut:
    return TicketService(db).assign_ticket(ticket_id, payload.assignee_id, current_user)


@router.patch("/{ticket_id}/status", response_model=TicketOut, summary="Change ticket status")
def change_status(
    ticket_id: int, payload: StatusUpdateRequest, db: DbSession, current_user: CurrentUser
) -> TicketOut:
    return TicketService(db).change_status(ticket_id, payload.status, current_user)


@router.patch("/{ticket_id}/close", response_model=TicketOut, summary="Close a resolved ticket")
def close_ticket(ticket_id: int, db: DbSession, current_user: CurrentUser) -> TicketOut:
    return TicketService(db).close_ticket(ticket_id, current_user)