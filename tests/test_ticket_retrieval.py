"""
Testing retrieval, filtering, searching and pagination
"""

def test_get_ticket_by_id(client, customer, make_ticket):
    ticket = make_ticket()

    response = client.get(f"/tickets/{ticket['id']}", headers=customer)

    assert response.status_code == 200
    assert response.json()["id"] == ticket["id"]


def test_get_unknown_ticket_returns_404(client, customer):
    response = client.get("/tickets/999", headers=customer)

    assert response.status_code == 404
    assert response.json()["code"] == "TICKET_NOT_FOUND"


def test_list_returns_paginated_envelope(client, customer, make_ticket):
    make_ticket(title="First issue")
    make_ticket(title="Second issue")

    body = client.get("/tickets", headers=customer).json()

    assert body["total"] == 2
    assert body["page"] == 1
    assert body["totalPages"] == 1
    assert len(body["items"]) == 2


def test_filter_by_status(client, customer, agent, make_ticket):
    open_ticket = make_ticket(title="Still open")
    other = make_ticket(title="Being worked on")
    client.patch(f"/tickets/{other['id']}/status", json={"status": "IN_PROGRESS"}, headers=agent)

    body = client.get("/tickets?status=OPEN", headers=customer).json()

    assert body["total"] == 1
    assert body["items"][0]["id"] == open_ticket["id"]


def test_filter_by_priority(client, customer, make_ticket):
    make_ticket(title="Urgent thing", priority="URGENT")
    make_ticket(title="Minor thing", priority="LOW")

    body = client.get("/tickets?priority=URGENT", headers=customer).json()

    assert body["total"] == 1
    assert body["items"][0]["title"] == "Urgent thing"


def test_filter_by_category(client, customer, make_ticket):
    make_ticket(title="Cable broken", category="HARDWARE")
    make_ticket(title="Cannot log in", category="ACCOUNT")

    body = client.get("/tickets?category=ACCOUNT", headers=customer).json()

    assert body["total"] == 1
    assert body["items"][0]["title"] == "Cannot log in"


def test_filter_by_assigned_agent(client, customer, agent, make_ticket):
    assigned = make_ticket(title="Assigned work")
    make_ticket(title="Unassigned work")
    client.patch(f"/tickets/{assigned['id']}/assign", json={"assigneeId": 3}, headers=agent)

    body = client.get("/tickets?assignedTo=3", headers=customer).json()

    assert body["total"] == 1
    assert body["items"][0]["id"] == assigned["id"]


def test_multiple_filters_are_combined(client, customer, make_ticket):
    make_ticket(title="Match", category="NETWORK", priority="HIGH")
    make_ticket(title="Wrong priority", category="NETWORK", priority="LOW")
    make_ticket(title="Wrong category", category="SOFTWARE", priority="HIGH")

    body = client.get("/tickets?category=NETWORK&priority=HIGH", headers=customer).json()

    assert body["total"] == 1
    assert body["items"][0]["title"] == "Match"


def test_search_by_title_is_case_insensitive(client, customer, make_ticket):
    make_ticket(title="Laptop will not boot")
    make_ticket(title="Mouse not working")

    upper = client.get("/tickets?search=LAPTOP", headers=customer).json()
    lower = client.get("/tickets?search=laptop", headers=customer).json()

    assert upper["total"] == 1
    assert lower["total"] == 1
    assert upper["items"][0]["title"] == "Laptop will not boot"


def test_search_matches_partial_titles(client, customer, make_ticket):
    make_ticket(title="Printer jammed again")

    body = client.get("/tickets?search=jam", headers=customer).json()

    assert body["total"] == 1


def test_search_with_no_matches_returns_empty_list(client, customer, make_ticket):
    make_ticket()

    body = client.get("/tickets?search=zzzzzzz", headers=customer).json()

    assert body["total"] == 0
    assert body["items"] == []


def test_pagination_splits_results(client, customer, make_ticket):
    for index in range(5):
        make_ticket(title=f"Issue number {index}")

    first = client.get("/tickets?page=1&pageSize=2", headers=customer).json()
    last = client.get("/tickets?page=3&pageSize=2", headers=customer).json()

    assert first["total"] == 5
    assert first["totalPages"] == 3
    assert len(first["items"]) == 2
    assert len(last["items"]) == 1


def test_page_size_above_maximum_is_rejected(client, customer):
    response = client.get("/tickets?pageSize=100000", headers=customer)

    assert response.status_code == 422


def test_sorting_by_title_ascending(client, customer, make_ticket):
    make_ticket(title="Zebra problem")
    make_ticket(title="Apple problem")

    body = client.get("/tickets?sortBy=title&order=asc", headers=customer).json()

    assert [t["title"] for t in body["items"]] == ["Apple problem", "Zebra problem"]


def test_unknown_sort_field_falls_back_to_default(client, customer, make_ticket):
    """An unrecognised sort column must not reach the query builder."""
    make_ticket(title="Only ticket")

    response = client.get("/tickets?sortBy=nonsense", headers=customer)

    assert response.status_code == 200
    assert response.json()["total"] == 1