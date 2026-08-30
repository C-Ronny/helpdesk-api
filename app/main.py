"""
Application entry point: builds the app, wires routers and handles errors
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.database import Base, SessionLocal, engine
from app.errors import AppError
from app.routers import comments, tickets, users
from app.seed import seed_users

DESCRIPTION = """
A support ticket system.

Authentication is out of scope. Identify yourself by sending an `X-User-Id`
header with every request; `GET /users` lists the seeded users and their roles.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_users(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Help Desk API",
        description=DESCRIPTION,
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        """Render every domain exception in one consistent shape."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Normalise FastAPI's validation errors into the same shape."""
        first = exc.errors()[0] if exc.errors() else {}
        location = ".".join(str(part) for part in first.get("loc", ())[1:]) or "request"
        message = first.get("msg", "Invalid request")
        return JSONResponse(
            status_code=422,
            content={
                "detail": f"{location}: {message}",
                "code": "VALIDATION_ERROR",
                "errors": [
                    {
                        "field": ".".join(str(p) for p in err.get("loc", ())[1:]),
                        "message": err.get("msg", ""),
                    }
                    for err in exc.errors()
                ],
            },
        )

    @app.get("/health", tags=["meta"], summary="Liveness check")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(users.router)
    app.include_router(tickets.router)
    app.include_router(comments.router)
    return app


app = create_app()