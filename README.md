# Help Desk API

A REST API for a help desk support ticket system. Customers file tickets, support agents triage, assign, progress and close them.

Built with FastAPI, SQLAlchemy and SQLite. 




## 1. Solution and architecture

The application uses a layered architecture and is organised in four layers. Each layer talks only to the one below it, which keeps business rules independent of both HTTP and the database.

```
HTTP request
    │
    ▼
Router      app/routers/      Parses the request, calls a service. No logic.
    │
    ▼
Service     app/services/     Every business rule. No knowledge of HTTP.
    │
    ▼
Repository  app/repositories/ All database access. The only layer using SQLAlchemy.
    │
    ▼
Database    SQLite
```

Two supporting concerns cut across those layers:

- **Schemas** (`app/schemas.py`) define the JSON contract, kept deliberately
  separate from the ORM models (`app/models.py`) that define storage.

- **Errors** (`app/errors.py`) are domain exceptions carrying an HTTP status
  code. Services raise them without importing FastAPI, and a single handler in
  `app/main.py` converts them into responses, so that business rules can be tested by calling a Python function, with no web server and no database.

### Project structure

```
helpdesk-api/
├── app/
│   ├── main.py              # App, Router wiring, error handlers
│   ├── config.py            # Settings and limits
│   ├── database.py          # Session factory, get_db dependency
│   ├── dependencies.py      # X-User-Id resolution
│   ├── enums.py             # Triage Data
│   ├── errors.py            # Domain exceptions
│   ├── models.py            # SQLAlchemy tables
│   ├── schemas.py           # Pydantic request/response models
│   ├── seed.py              # Demo users created at startup
│   ├── repositories/        # Data access
│   ├── routers/             # HTTP endpoints
│   └── services/            # Business rules
├── tests/                   # 71 tests
├── requirements.txt
└── pytest.ini
```

---

## 2. Technology choices

| Choice | Reason |
|---|---|
| **Python** | Fast to write |
| **FastAPI** | Request validation, typed responses and OpenAPI documentation come from the same type hints, so there is no separate schema to keep in sync. Swagger UI is generated automatically. |
| **SQLAlchemy** | A real ORM demonstrates data modelling (foreign keys, relationships, eager loading) rather than dictionary manipulation. |
| **SQLite** | An SQL database that does not need a server or installation, making it effective for a quick clone of the app and to be run immediately. |
| **pytest** | Fixtures make per-test database isolation concise. |

---

## 3. Installing dependencies

Requires Python 3.11 or newer.

***Install dependencies before running anything below — the application and the
tests both depend on them.***

```bash
git clone https://github.com/C-Ronny/helpdesk-api.git
cd helpdesk-api

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## 4. Running the application

```bash
python -m uvicorn app.main:app --reload
```

The API is served at `http://127.0.0.1:8000`.

- Interactive documentation: **http://127.0.0.1:8000/docs**
- Alternative documentation: http://127.0.0.1:8000/redoc

On first start the application creates `helpdesk.db` and seeds four users.
Delete that file to reset to a clean state.

### Seeded users

Authentication is out of scope. Every request identifies its caller with an
`X-User-Id` header. `GET /users` returns this list at runtime.

| id | Name | Role |
|---|---|---|
| 1 | Ama Mensah | CUSTOMER |
| 2 | Tobi Woode | CUSTOMER |
| 3 | Efua Owusu | AGENT |
| 4 | Eric Asare | AGENT |

---

## 5. Running the tests

```bash
python -m pytest
```

Expected: **71 passed**, 98% coverage.

Coverage is configured in `pytest.ini`, so no flags are needed. For an HTML
report:

```bash
pytest --cov=app --cov-report=html && open htmlcov/index.html
```

### What the tests cover

| File | Tests | Area |
|---|---|---|
| `test_ticket_creation.py` | 11 | Creation, field validation, header handling, author forgery |
| `test_ticket_retrieval.py` | 15 | Fetch, filter, search, pagination, sorting |
| `test_assignment.py` | 7 | Assignment rules and role restrictions |
| `test_status_transitions.py` | 12 | Lifecycle, invalid transitions, closing, reopening |
| `test_comments.py` | 9 | Comment validation and closed-ticket rules |
| `test_transition_rules.py` | 14 | The state machine itself, without HTTP or a database |
| `test_users_and_health.py` | 5 | Supporting endpoints and idempotent seeding |

Each test runs against a fresh in-memory database, so tests are independent and
order-insensitive.

---

## 6. API endpoints

All endpoints except `/health` and `/users` require an `X-User-Id` header.

| Method | Path | Description | Who |
|---|---|---|---|
| `POST` | `/tickets` | Create a ticket | Any user |
| `GET` | `/tickets` | List, filter, search, paginate | Any user |
| `GET` | `/tickets/{id}` | Fetch one ticket | Any user |
| `PATCH` | `/tickets/{id}/assign` | Assign to an agent | AGENT |
| `PATCH` | `/tickets/{id}/status` | Change status | AGENT |
| `PATCH` | `/tickets/{id}/close` | Close a resolved ticket | AGENT |
| `POST` | `/tickets/{id}/comments` | Add a comment | Any user |
| `GET` | `/tickets/{id}/comments` | List comments | Any user |
| `GET` | `/users` | List users | Any user |
| `GET` | `/users/{id}` | Fetch one user | Any user |
| `GET` | `/health` | Liveness check | Any user |

### Query parameters on `GET /tickets`

| Parameter | Values | Notes |
|---|---|---|
| `status` | OPEN, IN_PROGRESS, RESOLVED, CLOSED | |
| `priority` | LOW, MEDIUM, HIGH, URGENT | |
| `category` | HARDWARE, SOFTWARE, NETWORK, ACCOUNT, OTHER | |
| `assignedTo` | user id | |
| `search` | text | Case-insensitive partial match on title |
| `sortBy` | createdAt, updatedAt, priority, status, title | Default `createdAt` |
| `order` | asc, desc | Default `desc` |
| `page` | integer ≥ 1 | Default 1 |
| `pageSize` | 1–100 | Default 20 |

Multiple filters combine with AND.

### Status codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Ticket or comment created |
| 400 | Missing or malformed `X-User-Id`; a business rule violated |
| 403 | Caller's role does not permit the action |
| 404 | Ticket or user does not exist |
| 409 | Request valid, but the ticket's state does not allow it |
| 422 | Request body or query parameters failed validation |

Every error returns the same shape:

```json
{
  "detail": "Cannot transition from OPEN to CLOSED",
  "code": "INVALID_STATUS_TRANSITION"
}
```

---

## 7. Example requests and responses

### Create a ticket

```bash
curl -X POST localhost:8000/tickets \
  -H "X-User-Id: 1" -H "Content-Type: application/json" \
  -d '{
        "title": "Laptop will not boot",
        "description": "Black screen on startup",
        "category": "HARDWARE",
        "priority": "HIGH"
      }'
```

`201 Created`

```json
{
  "id": 1,
  "title": "Laptop will not boot",
  "description": "Black screen on startup",
  "priority": "HIGH",
  "status": "OPEN",
  "category": "HARDWARE",
  "createdBy": {
    "id": 1,
    "name": "Ama Mensah",
    "email": "ama@example.com",
    "role": "CUSTOMER"
  },
  "assignedTo": null,
  "createdAt": "2026-08-30T15:59:35.298617",
  "updatedAt": "2026-08-30T15:59:35.298624"
}
```

### Search and filter

```bash
curl "localhost:8000/tickets?search=LAPTOP&priority=HIGH&page=1&pageSize=20" \
  -H "X-User-Id: 1"
```

`200 OK`

```json
{
  "items": [ { "id": 1, "title": "Laptop will not boot", "...": "..." } ],
  "total": 1,
  "page": 1,
  "pageSize": 20,
  "totalPages": 1
}
```

### Assign to an agent

```bash
curl -X PATCH localhost:8000/tickets/1/assign \
  -H "X-User-Id: 3" -H "Content-Type: application/json" \
  -d '{"assigneeId": 4}'
```

Assigning to a customer returns `400`:

```json
{
  "detail": "Tickets can only be assigned to users with the AGENT role",
  "code": "ASSIGNEE_NOT_AGENT"
}
```

### Change status

```bash
curl -X PATCH localhost:8000/tickets/1/status \
  -H "X-User-Id: 3" -H "Content-Type: application/json" \
  -d '{"status": "IN_PROGRESS"}'
```

Skipping a stage returns `409`:

```json
{
  "detail": "Cannot transition from OPEN to CLOSED",
  "code": "INVALID_STATUS_TRANSITION"
}
```

### Close a ticket

```bash
curl -X PATCH localhost:8000/tickets/1/close -H "X-User-Id: 3"
```

A customer attempting this returns `403`:

```json
{
  "detail": "Only users with the AGENT role can change ticket status",
  "code": "AGENT_ROLE_REQUIRED"
}
```

### Add a comment

```bash
curl -X POST localhost:8000/tickets/1/comments \
  -H "X-User-Id: 1" -H "Content-Type: application/json" \
  -d '{"body": "Any update on this?"}'
```

`201 Created`

```json
{
  "id": 1,
  "ticketId": 1,
  "body": "Any update on this?",
  "author": {
    "id": 1,
    "name": "Ama Mensah",
    "email": "ama@example.com",
    "role": "CUSTOMER"
  },
  "createdAt": "2026-08-30T16:04:11.882410"
}
```

### Validation failure

```bash
curl -X POST localhost:8000/tickets \
  -H "X-User-Id: 1" -H "Content-Type: application/json" \
  -d '{"title": "'"$(printf 'A%.0s' {1..101})"'", "description": "x", "category": "OTHER"}'
```

`422 Unprocessable Entity`

```json
{
  "detail": "title: String should have at most 100 characters",
  "code": "VALIDATION_ERROR",
  "errors": [
    { "field": "title", "message": "String should have at most 100 characters" }
  ]
}
```

---

## 8. Design decisions

**The status lifecycle is a single table.** `ALLOWED_TRANSITIONS` in `app/enums.py` maps each status to the set it may move to:

| From | To |
|---|---|
| OPEN | IN_PROGRESS |
| IN_PROGRESS | RESOLVED |
| RESOLVED | CLOSED, IN_PROGRESS |
| CLOSED | *(terminal)* |

 CLOSED is unreachable except from RESOLVED, so "a ticket can only be closed after it has been resolved" is guaranteed by the shape of the data. `RESOLVED → IN_PROGRESS` allows reopening if a fix did not work.

**`/close` and `/status` share one implementation.** `close_ticket()` delegates to `change_status()` with `CLOSED`. The specification requires both endpoints, so the two can never diverge.

**Agents own the lifecycle.** The specification explicitly requires only that assignees be agents. This implementation ensures that: assigning, changing status and closing tickets are agent-only, since customers create the tickets and the agents manage them. Customers can create tickets and comment.

**Errors are domain exceptions, not HTTP exceptions.** Services raise `NotFoundError`, `ForbiddenError`, `ConflictError` or `BusinessRuleError`. Each carries a status code that a handler in `main.py` reads. 

An invalid transition is not a distorted request, so 409 Conflict says the request was fine but the resource is in an incompatible state.

`Tickets reference users by id.`

**Pagination has a stable secondary sort.** Results order by the chosen column
then by descending id, so tickets created in the same instant cannot appear
twice or vanish across pages.

---

## 9. Assumptions

1. **Anyone may read any ticket.** The specification does not restrict visibility, and restricting customers to their own tickets would complicate the required filtering endpoints without being asked for.
2. **A customer may not comment on a closed ticket; an agent may.** Once a ticket is closed, only agents can still annotate for the record.
3. **Missing `X-User-Id` returns 400, not 401.** Because authentication is out of scope, 401 would imply a login mechanism that does not exist.
4. **An unknown `X-User-Id` returns 404**.
5. **Users are seeded, not created via the API.** No user-creation endpoint is specified. `GET /users` was added so a reviewer can discover valid ids without reading the source.
6. **Assignment does not change status.** A ticket stays OPEN until an agent explicitly moves it, keeping state changes observable.
7. **Setting a ticket to its current status returns 409.** A no-op status change indicating a client bug than an intent.
8. **A closed ticket cannot be reassigned.**
9. **Comments do not update the ticket's `updatedAt`.** That field tracks changes to the ticket itself.
10. **Length limits are enforced by Pydantic model, not the database.** SQLite does not enforce `VARCHAR` lengths; validation happens at the boundary, before any data reaches storage.
11. **Search matches titles only**, as specified, using a case-insensitive substring match.

---

## 10. Known limitations

- **No authentication.** The `X-User-Id` header is trusted completely. Any caller can claim to be any user. This is by design, and would be unacceptable in production.
- **No database migrations.** Tables are created with `create_all()` at startup. A production system would allow schema changes to be versioned.
- **SQLite is single-writer.** A concurrent deployment would need PostgreSQL. Only the connection string would change.
- **Offset pagination degrades on very large tables.** Cursor pagination would scale better but adds complexity.
- **Search uses `LIKE`**, which cannot use an index for a leading wildcard. Full text search would be the answer at scale.
- **No soft deletes or audit trail.** Status history is not retained; only the current status and `updatedAt` are stored.
- **No `PUT`/`PATCH` for editing a ticket's title, description, priority or category** — not among the required endpoints.
- **Seed data is fixed.** Adding users requires editing `app/seed.py`.
