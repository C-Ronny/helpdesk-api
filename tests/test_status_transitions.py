"""
Status changes and closing tests
"""

import pytest


def test_full_lifecycle_is_permitted(client, agent, make_ticket):
    ticket = make_ticket()

    for status in ("IN_PROGRESS", "RESOLVED", "CLOSED"):
        response = client.patch(
            f"/tickets/{ticket['id']}/status", json={"status": status}, headers=agent
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == status


@pytest.mark.parametrize("target", ["RESOLVED", "CLOSED"])
def test_open_ticket_cannot_skip_ahead(client, agent, make_ticket, target):
    """Business rule 5: a ticket may not jump over intermediate states."""
    ticket = make_ticket()

    response = client.patch(
        f"/tickets/{ticket['id']}/status", json={"status": target}, headers=agent
    )

    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATUS_TRANSITION"


def test_close_endpoint_rejects_an_unresolved_ticket(client, agent, make_ticket):
    """Business rule 4: closing requires the ticket to be RESOLVED first."""
    ticket = make_ticket()

    response = client.patch(f"/tickets/{ticket['id']}/close", headers=agent)

    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATUS_TRANSITION"


def test_resolved_ticket_can_be_closed(client, agent, resolved_ticket):
    response = client.patch(f"/tickets/{resolved_ticket['id']}/close", headers=agent)

    assert response.status_code == 200
    assert response.json()["status"] == "CLOSED"


def test_resolved_ticket_can_be_reopened(client, agent, resolved_ticket):
    response = client.patch(
        f"/tickets/{resolved_ticket['id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=agent,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


def test_closed_ticket_is_terminal(client, agent, resolved_ticket):
    client.patch(f"/tickets/{resolved_ticket['id']}/close", headers=agent)

    response = client.patch(
        f"/tickets/{resolved_ticket['id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=agent,
    )

    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATUS_TRANSITION"


def test_setting_the_current_status_again_is_rejected(client, agent, make_ticket):
    ticket = make_ticket()

    response = client.patch(
        f"/tickets/{ticket['id']}/status", json={"status": "OPEN"}, headers=agent
    )

    assert response.status_code == 409
    assert response.json()["code"] == "NO_STATUS_CHANGE"


def test_customer_cannot_change_status(client, customer, make_ticket):
    ticket = make_ticket()

    response = client.patch(
        f"/tickets/{ticket['id']}/status", json={"status": "IN_PROGRESS"}, headers=customer
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AGENT_ROLE_REQUIRED"


def test_customer_cannot_close_a_ticket(client, customer, resolved_ticket):
    response = client.patch(f"/tickets/{resolved_ticket['id']}/close", headers=customer)

    assert response.status_code == 403


def test_invalid_status_value_is_rejected(client, agent, make_ticket):
    ticket = make_ticket()

    response = client.patch(
        f"/tickets/{ticket['id']}/status", json={"status": "PENDING"}, headers=agent
    )

    assert response.status_code == 422


def test_status_change_on_unknown_ticket_returns_404(client, agent):
    response = client.patch("/tickets/999/status", json={"status": "IN_PROGRESS"}, headers=agent)

    assert response.status_code == 404
    assert response.json()["code"] == "TICKET_NOT_FOUND"