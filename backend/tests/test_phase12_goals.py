from fastapi.testclient import TestClient


def signup(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "display_name": "Goals User",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    cookie = client.cookies.get("ledger_session")
    assert cookie is not None
    return cookie


def test_goal_crud_progress_status_and_dashboard(client: TestClient) -> None:
    first_cookie = signup(client, "goals@example.com")
    response = client.post(
        "/api/v1/goals",
        json={
            "name": "New Laptop",
            "target_amount_cad": "2000.00",
            "current_amount_cad": "850.00",
            "target_date": "2027-01-31",
        },
    )
    assert response.status_code == 201
    goal = response.json()
    assert goal["remaining_amount_cad"] == "1150.00"
    assert goal["percentage_complete"] == "42.50"
    assert goal["status"] == "active"

    updated = client.patch(
        f"/api/v1/goals/{goal['id']}", json={"current_amount_cad": "2000.00"}
    )
    assert updated.status_code == 200
    assert updated.json()["percentage_complete"] == "100.00"
    assert updated.json()["remaining_amount_cad"] == "0.00"
    assert updated.json()["status"] == "completed"

    dashboard = client.get("/api/v1/dashboard", params={"month": "2026-09"}).json()
    assert [item["name"] for item in dashboard["goals"]] == ["New Laptop"]
    assert dashboard["goals"][0]["status"] == "completed"

    assert client.post(
        "/api/v1/goals",
        json={"name": "New Laptop", "target_amount_cad": "100.00"},
    ).status_code == 409
    assert client.post(
        "/api/v1/goals",
        json={"name": "Invalid", "target_amount_cad": "0"},
    ).status_code == 422
    assert client.post(
        "/api/v1/goals",
        json={
            "name": "Invalid progress",
            "target_amount_cad": "100.00",
            "current_amount_cad": "-1.00",
        },
    ).status_code == 422

    client.cookies.clear()
    signup(client, "other-goals@example.com")
    assert client.get(f"/api/v1/goals/{goal['id']}").status_code == 404
    assert client.patch(
        f"/api/v1/goals/{goal['id']}", json={"current_amount_cad": "1.00"}
    ).status_code == 404

    client.cookies.set("ledger_session", first_cookie)
    assert client.delete(f"/api/v1/goals/{goal['id']}").status_code == 204
    assert client.get(f"/api/v1/goals/{goal['id']}").status_code == 404


def test_paused_and_cancelled_goals_preserve_explicit_status(client: TestClient) -> None:
    signup(client, "goal-status@example.com")
    paused = client.post(
        "/api/v1/goals",
        json={
            "name": "Vacation",
            "target_amount_cad": "500.00",
            "current_amount_cad": "500.00",
            "status": "paused",
        },
    )
    assert paused.status_code == 201
    assert paused.json()["status"] == "paused"
    cancelled = client.post(
        "/api/v1/goals",
        json={"name": "Old plan", "target_amount_cad": "100.00", "status": "cancelled"},
    )
    assert cancelled.status_code == 201
    dashboard = client.get("/api/v1/dashboard").json()
    assert [item["name"] for item in dashboard["goals"]] == ["Vacation"]
