from fastapi.testclient import TestClient


def signup(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "display_name": "Phase Nine",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    cookie = client.cookies.get("ledger_session")
    assert cookie is not None
    return cookie


def add_event(
    client: TestClient,
    person_id: str,
    event_type: str,
    amount: str,
    event_date: str,
    adjustment_direction: str | None = None,
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/people/{person_id}/events",
        json={
            "event_type": event_type,
            "amount_cad": amount,
            "date": event_date,
            "adjustment_direction": adjustment_direction,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_people_balances_are_derived_from_complete_event_history(
    client: TestClient,
) -> None:
    signup(client, "people@example.com")
    alex = client.post(
        "/api/v1/people", json={"name": "Alex", "notes": "Roommate"}
    ).json()
    sam = client.post("/api/v1/people", json={"name": "Sam"}).json()

    add_event(client, alex["id"], "borrowed", "100.00", "2026-09-01")
    repayment = add_event(
        client, alex["id"], "repayment_made", "40.00", "2026-09-10"
    )
    adjustment = add_event(
        client,
        alex["id"],
        "adjustment",
        "20.00",
        "2026-09-12",
        "owes_user",
    )
    add_event(client, sam["id"], "lent", "200.00", "2026-09-02")
    add_event(client, sam["id"], "repayment_received", "50.00", "2026-09-11")

    people = client.get("/api/v1/people").json()
    summary_rows = [
        (item["name"], item["direction"], item["outstanding_amount_cad"])
        for item in people
    ]
    assert summary_rows == [
        ("Alex", "user_owes", "40.00"),
        ("Sam", "owed_to_user", "150.00"),
    ]
    assert people[0]["last_activity"] == "2026-09-12"
    assert people[0]["event_count"] == 3

    detail = client.get(f"/api/v1/people/{alex['id']}").json()
    assert detail["notes"] == "Roommate"
    assert [event["event_type"] for event in detail["events"]] == [
        "adjustment",
        "repayment_made",
        "borrowed",
    ]
    assert [event["running_balance_cad"] for event in detail["events"]] == [
        "-40.00",
        "-60.00",
        "-100.00",
    ]

    updated = client.patch(
        f"/api/v1/people/{alex['id']}/events/{repayment['id']}",
        json={"amount_cad": "50.00"},
    )
    assert updated.status_code == 200
    assert updated.json()["running_balance_cad"] == "-50.00"

    dashboard = client.get("/api/v1/dashboard", params={"month": "2026-09"}).json()
    assert dashboard["summary"]["money_owed_to_user_cad"] == "150.00"
    assert dashboard["summary"]["money_owed_to_others_cad"] == "30.00"

    assert (
        client.delete(
            f"/api/v1/people/{alex['id']}/events/{adjustment['id']}"
        ).status_code
        == 204
    )
    alex_after_delete = client.get(f"/api/v1/people/{alex['id']}").json()
    assert alex_after_delete["outstanding_amount_cad"] == "50.00"


def test_people_validation_ownership_and_cascade_delete(client: TestClient) -> None:
    first_cookie = signup(client, "owner@example.com")
    person_response = client.post("/api/v1/people", json={"name": "Taylor"})
    assert person_response.status_code == 201
    person = person_response.json()
    event = add_event(client, person["id"], "lent", "25.00", "2026-09-01")

    assert client.post("/api/v1/people", json={"name": "Taylor"}).status_code == 409
    assert client.post("/api/v1/people", json={"name": "   "}).status_code == 422
    assert client.patch(
        f"/api/v1/people/{person['id']}", json={"name": None}
    ).status_code == 422
    assert client.post(
        f"/api/v1/people/{person['id']}/events",
        json={"event_type": "adjustment", "amount_cad": "10.00", "date": "2026-09-02"},
    ).status_code == 422
    assert client.post(
        f"/api/v1/people/{person['id']}/events",
        json={
            "event_type": "lent",
            "amount_cad": "10.00",
            "date": "2026-09-02",
            "adjustment_direction": "owes_user",
        },
    ).status_code == 422
    assert client.post(
        f"/api/v1/people/{person['id']}/events",
        json={"event_type": "borrowed", "amount_cad": "0", "date": "2026-09-02"},
    ).status_code == 422

    client.cookies.clear()
    signup(client, "other-owner@example.com")
    assert client.get(f"/api/v1/people/{person['id']}").status_code == 404
    assert client.patch(
        f"/api/v1/people/{person['id']}/events/{event['id']}",
        json={"amount_cad": "100.00"},
    ).status_code == 404

    client.cookies.set("ledger_session", first_cookie)
    assert client.delete(f"/api/v1/people/{person['id']}").status_code == 204
    assert client.get(f"/api/v1/people/{person['id']}").status_code == 404
