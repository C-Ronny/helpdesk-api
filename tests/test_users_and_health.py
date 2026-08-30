"""
Supporting endpoints
"""

def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_users_returns_seeded_accounts(client):
    response = client.get("/users")

    assert response.status_code == 200
    users = response.json()
    assert len(users) == 4
    assert {u["role"] for u in users} == {"CUSTOMER", "AGENT"}


def test_get_unknown_user_returns_404(client):
    response = client.get("/users/999")

    assert response.status_code == 404
    assert response.json()["code"] == "USER_NOT_FOUND"


def test_get_single_user(client):
    response = client.get("/users/3")

    assert response.status_code == 200
    assert response.json()["role"] == "AGENT"


def test_seeding_is_idempotent(client, db_session):
    """Re-seeding an already populated database must not duplicate users."""
    from app.seed import seed_users

    seed_users(db_session)

    assert len(client.get("/users").json()) == 4