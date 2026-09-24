from fastapi.testclient import TestClient


def signup(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "display_name": "Budget User",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    cookie = client.cookies.get("ledger_session")
    assert cookie is not None
    return cookie


def test_budget_crud_progress_dashboard_and_ownership(client: TestClient) -> None:
    first_cookie = signup(client, "budget@example.com")
    account = client.post(
        "/api/v1/accounts",
        json={"name": "Budget chequing", "type": "chequing", "currency": "CAD"},
    ).json()
    catalog = client.get("/api/v1/classifications").json()
    essentials = next(item for item in catalog["buckets"] if item["name"] == "Essentials")
    groceries = next(item for item in essentials["categories"] if item["name"] == "Groceries")

    for amount, transaction_date, description in (
        ("120.00", "2026-09-04", "September groceries"),
        ("50.00", "2026-10-04", "October groceries"),
    ):
        response = client.post(
            "/api/v1/transactions",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount_cad": amount,
                "date": transaction_date,
                "description": description,
                "bucket_id": essentials["id"],
                "category_id": groceries["id"],
            },
        )
        assert response.status_code == 201

    created = client.post(
        "/api/v1/budgets",
        json={
            "month": "2026-09",
            "amount_cad": "100.00",
            "bucket_id": essentials["id"],
        },
    )
    assert created.status_code == 201
    budget = created.json()
    assert budget["scope_type"] == "bucket"
    assert budget["scope_name"] == "Essentials"
    assert budget["period_start"] == "2026-09-01"
    assert budget["period_end"] == "2026-09-30"
    assert budget["spent_cad"] == "120.00"
    assert budget["remaining_cad"] == "-20.00"
    assert budget["percentage_used"] == "120.0"
    assert budget["is_over_budget"] is True

    duplicate = client.post(
        "/api/v1/budgets",
        json={
            "month": "2026-09",
            "amount_cad": "300.00",
            "bucket_id": essentials["id"],
        },
    )
    assert duplicate.status_code == 409

    category_budget = client.post(
        "/api/v1/budgets",
        json={
            "month": "2026-09",
            "amount_cad": "240.00",
            "category_id": groceries["id"],
        },
    )
    assert category_budget.status_code == 201
    assert category_budget.json()["percentage_used"] == "50.0"

    listed = client.get("/api/v1/budgets", params={"month": "2026-09"}).json()
    assert len(listed) == 2
    assert client.get("/api/v1/budgets", params={"month": "2026-10"}).json() == []

    updated = client.patch(
        f"/api/v1/budgets/{budget['id']}", json={"amount_cad": "150.00"}
    )
    assert updated.status_code == 200
    assert updated.json()["remaining_cad"] == "30.00"
    assert updated.json()["percentage_used"] == "80.0"
    assert updated.json()["is_over_budget"] is False

    dashboard = client.get("/api/v1/dashboard", params={"month": "2026-09"}).json()
    assert len(dashboard["budget_progress"]) == 2

    client.cookies.clear()
    signup(client, "other-budget@example.com")
    assert client.get(f"/api/v1/budgets/{budget['id']}").status_code == 404
    foreign_scope = client.post(
        "/api/v1/budgets",
        json={
            "month": "2026-09",
            "amount_cad": "50.00",
            "bucket_id": essentials["id"],
        },
    )
    assert foreign_scope.status_code == 422

    client.cookies.set("ledger_session", first_cookie)
    assert client.delete(f"/api/v1/budgets/{budget['id']}").status_code == 204
    assert client.get(f"/api/v1/budgets/{budget['id']}").status_code == 404


def test_budget_requires_one_valid_scope_and_month(client: TestClient) -> None:
    signup(client, "budget-validation@example.com")
    assert client.post(
        "/api/v1/budgets", json={"month": "2026-09", "amount_cad": "100.00"}
    ).status_code == 422
    assert client.post(
        "/api/v1/budgets", json={"month": "0000-01", "amount_cad": "100.00"}
    ).status_code == 422
    assert client.get("/api/v1/budgets", params={"month": "invalid"}).status_code == 422
