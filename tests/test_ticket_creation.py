"""
Ticket creation and input validation
"""

def test_create_ticket_returns_201_and_defaults_to_open(client, customer):
    response = client.post(
        "/tickets",
        json={
            "title": "Printer jammed",
            "description": "Paper stuck in tray 2",
            "category": "HARDWARE",
            "priority": "HIGH",
        },
        headers=customer,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "OPEN"
    assert body["assignedTo"] is None
    assert body["createdBy"]["id"] == 1
    assert body["createdAt"] is not None


def test_priority_defaults_to_medium_when_omitted(client, customer):
    response = client.post(
        "/tickets",
        json={"title": "VPN drops", "description": "Every ten minutes", "category": "NETWORK"},
        headers=customer,
    )

    assert response.status_code == 201
    assert response.json()["priority"] == "MEDIUM"


def test_title_longer_than_100_characters_is_rejected(client, customer):
    response = client.post(
        "/tickets",
        json={"title": "A" * 101, "description": "Too long a title", "category": "OTHER"},
        headers=customer,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_description_longer_than_1000_characters_is_rejected(client, customer):
    response = client.post(
        "/tickets",
        json={"title": "Fine", "description": "D" * 1001, "category": "OTHER"},
        headers=customer,
    )

    assert response.status_code == 422


def test_blank_title_is_rejected(client, customer):
    """Whitespace passes a length check but is still empty input."""
    response = client.post(
        "/tickets",
        json={"title": "   ", "description": "Real description", "category": "OTHER"},
        headers=customer,
    )

    assert response.status_code == 422


def test_missing_description_is_rejected(client, customer):
    response = client.post(
        "/tickets", json={"title": "No description", "category": "OTHER"}, headers=customer
    )

    assert response.status_code == 422


def test_invalid_category_is_rejected(client, customer):
    response = client.post(
        "/tickets",
        json={"title": "Bad category", "description": "...", "category": "TELEPATHY"},
        headers=customer,
    )

    assert response.status_code == 422


def test_missing_user_header_is_rejected(client):
    response = client.post(
        "/tickets", json={"title": "Anonymous", "description": "...", "category": "OTHER"}
    )

    assert response.status_code == 400
    assert response.json()["code"] == "MISSING_USER_HEADER"


def test_unknown_user_returns_404(client):
    response = client.post(
        "/tickets",
        json={"title": "Ghost", "description": "...", "category": "OTHER"},
        headers={"X-User-Id": "999"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "USER_NOT_FOUND"


def test_non_numeric_user_header_is_rejected(client):
    response = client.post(
        "/tickets",
        json={"title": "Bad header", "description": "...", "category": "OTHER"},
        headers={"X-User-Id": "not-a-number"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_USER_HEADER"


def test_author_cannot_be_forged_via_request_body(client, customer):
    """createdBy comes from the header; a body field must not override it."""
    response = client.post(
        "/tickets",
        json={
            "title": "Impersonation attempt",
            "description": "...",
            "category": "OTHER",
            "createdBy": 4,
            "status": "CLOSED",
        },
        headers=customer,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["createdBy"]["id"] == 1
    assert body["status"] == "OPEN"