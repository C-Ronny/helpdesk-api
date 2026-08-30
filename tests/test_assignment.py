"""
Ticket assignment
"""


def test_agent_can_assign_ticket_to_an_agent(client, agent, make_ticket):
    ticket = make_ticket()

    response = client.patch(
        f"/tickets/{ticket['id']}/assign", json={"assigneeId": 4}, headers=agent
    )

    assert response.status_code == 200
    assert response.json()["assignedTo"]["id"] == 4
    assert response.json()["assignedTo"]["role"] == "AGENT"


def test_customer_cannot_assign_tickets(client, customer, make_ticket):
    ticket = make_ticket()

    response = client.patch(
        f"/tickets/{ticket['id']}/assign", json={"assigneeId": 3}, headers=customer
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AGENT_ROLE_REQUIRED"


def test_ticket_cannot_be_assigned_to_a_customer(client, agent, make_ticket):
    """Business rule 3: only AGENT users may be assignees."""
    ticket = make_ticket()

    response = client.patch(
        f"/tickets/{ticket['id']}/assign", json={"assigneeId": 1}, headers=agent
    )

    assert response.status_code == 400
    assert response.json()["code"] == "ASSIGNEE_NOT_AGENT"


def test_assigning_to_unknown_user_returns_404(client, agent, make_ticket):
    ticket = make_ticket()

    response = client.patch(
        f"/tickets/{ticket['id']}/assign", json={"assigneeId": 999}, headers=agent
    )

    assert response.status_code == 404
    assert response.json()["code"] == "USER_NOT_FOUND"


def test_assigning_unknown_ticket_returns_404(client, agent):
    response = client.patch("/tickets/999/assign", json={"assigneeId": 3}, headers=agent)

    assert response.status_code == 404
    assert response.json()["code"] == "TICKET_NOT_FOUND"


def test_ticket_can_be_reassigned(client, agent, make_ticket):
    ticket = make_ticket()
    client.patch(f"/tickets/{ticket['id']}/assign", json={"assigneeId": 3}, headers=agent)

    response = client.patch(
        f"/tickets/{ticket['id']}/assign", json={"assigneeId": 4}, headers=agent
    )

    assert response.status_code == 200
    assert response.json()["assignedTo"]["id"] == 4


def test_closed_ticket_cannot_be_reassigned(client, agent, resolved_ticket):
    client.patch(f"/tickets/{resolved_ticket['id']}/close", headers=agent)

    response = client.patch(
        f"/tickets/{resolved_ticket['id']}/assign", json={"assigneeId": 3}, headers=agent
    )

    assert response.status_code == 409
    assert response.json()["code"] == "TICKET_CLOSED"