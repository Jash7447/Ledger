from fastapi.testclient import TestClient


def signup(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "display_name": "Dashboard User",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    cookie = client.cookies.get("ledger_session")
    assert cookie is not None
    return cookie


def test_dashboard_aggregates_transactions_without_counting_transfers(client: TestClient) -> None:
    first_cookie = signup(client, "dashboard@example.com")
    chequing = client.post(
        "/api/v1/accounts",
        json={"name": "Dashboard chequing", "type": "chequing", "currency": "CAD"},
    ).json()
    savings = client.post(
        "/api/v1/accounts",
        json={"name": "Dashboard savings", "type": "savings", "currency": "CAD"},
    ).json()
    catalog = client.get("/api/v1/classifications").json()
    essentials = next(item for item in catalog["buckets"] if item["name"] == "Essentials")
    education = next(item for item in catalog["buckets"] if item["name"] == "Education")
    groceries = next(item for item in essentials["categories"] if item["name"] == "Groceries")
    books = next(item for item in education["categories"] if item["name"] == "Books")
    salary = next(item for item in catalog["income_categories"] if item["name"] == "Salary")

    transactions = [
        {
            "account_id": chequing["id"],
            "type": "income",
            "amount_cad": "1000.00",
            "date": "2026-09-01",
            "description": "September salary",
            "category_id": salary["id"],
        },
        {
            "account_id": chequing["id"],
            "type": "expense",
            "amount_cad": "200.00",
            "date": "2026-09-02",
            "description": "Monthly groceries",
            "bucket_id": essentials["id"],
            "category_id": groceries["id"],
        },
        {
            "account_id": chequing["id"],
            "type": "expense",
            "amount_cad": "300.00",
            "date": "2026-09-03",
            "description": "Course books",
            "bucket_id": education["id"],
            "category_id": books["id"],
            "is_major_purchase": True,
        },
        {
            "account_id": chequing["id"],
            "destination_account_id": savings["id"],
            "type": "transfer",
            "amount_cad": "100.00",
            "date": "2026-09-04",
            "description": "Savings transfer",
        },
        {
            "account_id": chequing["id"],
            "type": "expense",
            "amount_cad": "50.00",
            "date": "2026-08-20",
            "description": "Previous month",
            "bucket_id": essentials["id"],
            "category_id": groceries["id"],
        },
    ]
    for transaction in transactions:
        assert client.post("/api/v1/transactions", json=transaction).status_code == 201

    response = client.get("/api/v1/dashboard", params={"month": "2026-09"})
    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["period_start"] == "2026-09-01"
    assert dashboard["period_end"] == "2026-09-30"
    assert dashboard["summary"] == {
        "current_balance_cad": "450.00",
        "monthly_income_cad": "1000.00",
        "monthly_expenses_cad": "500.00",
        "monthly_savings_cad": "500.00",
        "education_spending_cad": "300.00",
        "money_owed_to_user_cad": "0.00",
        "money_owed_to_others_cad": "0.00",
    }
    assert [(item["name"], item["amount_cad"]) for item in dashboard["spending_by_bucket"]] == [
        ("Education", "300.00"),
        ("Essentials", "200.00"),
    ]
    assert dashboard["spending_by_category"][0]["name"] == "Books"
    assert dashboard["recent_transactions"][0]["description"] == "Savings transfer"
    assert [item["description"] for item in dashboard["major_purchases"]] == [
        "Course books"
    ]

    client.cookies.clear()
    signup(client, "empty-dashboard@example.com")
    empty = client.get("/api/v1/dashboard", params={"month": "2026-09"}).json()
    assert empty["summary"]["current_balance_cad"] == "0.00"
    assert empty["summary"]["monthly_income_cad"] == "0.00"
    assert empty["recent_transactions"] == []

    client.cookies.set("ledger_session", first_cookie)
    assert client.get("/api/v1/dashboard", params={"month": "not-a-month"}).status_code == 422
    assert client.get("/api/v1/dashboard", params={"month": "0000-01"}).status_code == 422
