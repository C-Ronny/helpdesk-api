"""
Comments Tests
"""


def test_customer_can_comment_on_their_ticket(client, customer, make_ticket):
    ticket = make_ticket()

    response = client.post(
        f"/tickets/{ticket['id']}/comments", json={"body": "Any update?"}, headers=customer
    )

    assert response.status_code == 201
    body = response.json()
    assert body["body"] == "Any update?"
    assert body["author"]["id"] == 1
    assert body["ticketId"] == ticket["id"]


def test_empty_comment_is_rejected(client, customer, make_ticket):
    ticket = make_ticket()

    response = client.post(
        f"/tickets/{ticket['id']}/comments", json={"body": "   "}, headers=customer
    )

    assert response.status_code == 422


def test_comment_longer_than_1000_characters_is_rejected(client, customer, make_ticket):
    ticket = make_ticket()

    response = client.post(
        f"/tickets/{ticket['id']}/comments", json={"body": "x" * 1001}, headers=customer
    )

    assert response.status_code == 422


def test_comment_on_unknown_ticket_returns_404(client, customer):
    response = client.post("/tickets/999/comments", json={"body": "Hello"}, headers=customer)

    assert response.status_code == 404
    assert response.json()["code"] == "TICKET_NOT_FOUND"


def test_comments_are_listed_oldest_first(client, customer, agent, make_ticket):
    ticket = make_ticket()
    client.post(f"/tickets/{ticket['id']}/comments", json={"body": "First"}, headers=customer)
    client.post(f"/tickets/{ticket['id']}/comments", json={"body": "Second"}, headers=agent)

    response = client.get(f"/tickets/{ticket['id']}/comments", headers=customer)

    assert response.status_code == 200
    assert [c["body"] for c in response.json()] == ["First", "Second"]


def test_listing_comments_on_unknown_ticket_returns_404(client, customer):
    """An empty list would wrongly imply the ticket exists."""
    response = client.get("/tickets/999/comments", headers=customer)

    assert response.status_code == 404


def test_customer_cannot_comment_on_a_closed_ticket(client, customer, agent, resolved_ticket):
    client.patch(f"/tickets/{resolved_ticket['id']}/close", headers=agent)

    response = client.post(
        f"/tickets/{resolved_ticket['id']}/comments",
        json={"body": "Reopening this"},
        headers=customer,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "TICKET_CLOSED"


def test_agent_can_still_comment_on_a_closed_ticket(client, agent, resolved_ticket):
    client.patch(f"/tickets/{resolved_ticket['id']}/close", headers=agent)

    response = client.post(
        f"/tickets/{resolved_ticket['id']}/comments",
        json={"body": "Archived for the record"},
        headers=agent,
    )

    assert response.status_code == 201


def test_comment_requires_a_user_header(client, make_ticket):
    ticket = make_ticket()

    response = client.post(f"/tickets/{ticket['id']}/comments", json={"body": "Anonymous"})

    assert response.status_code == 400