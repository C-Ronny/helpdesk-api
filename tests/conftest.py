"""
Each test gets a fresh in-memory database
They never see each other's data and can run in any order.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import create_app
from app.seed import seed_users

CUSTOMER_ID = 1
SECOND_CUSTOMER_ID = 2
AGENT_ID = 3
SECOND_AGENT_ID = 4


@pytest.fixture
def db_session() -> Session:
    """An isolated in-memory database, seeded with the standard users."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        # StaticPool keeps every connection pointed at the same in-memory
        # database; without it each connection would get its own empty one.
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = TestingSession()
    seed_users(db)
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """A test client wired to the isolated database.

    TestClient is used without a context manager on purpose: that skips the
    lifespan hook, so tests never touch the real on-disk database file.
    """
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def customer() -> dict[str, str]:
    return {"X-User-Id": str(CUSTOMER_ID)}


@pytest.fixture
def agent() -> dict[str, str]:
    return {"X-User-Id": str(AGENT_ID)}


@pytest.fixture
def make_ticket(client: TestClient, customer: dict[str, str]):
    """Factory for creating a ticket as a customer and returning its JSON."""

    def _make(**overrides) -> dict:
        payload = {
            "title": "Laptop will not boot",
            "description": "Black screen on startup",
            "category": "HARDWARE",
            "priority": "HIGH",
        } | overrides
        response = client.post("/tickets", json=payload, headers=customer)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def resolved_ticket(client: TestClient, agent: dict[str, str], make_ticket):
    """A ticket walked through the lifecycle up to RESOLVED."""
    ticket = make_ticket()
    for status in ("IN_PROGRESS", "RESOLVED"):
        response = client.patch(
            f"/tickets/{ticket['id']}/status", json={"status": status}, headers=agent
        )
        assert response.status_code == 200, response.text
    return response.json()