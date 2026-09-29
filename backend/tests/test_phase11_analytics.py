from fastapi.testclient import TestClient


def signup(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "display_name": "Analytics User",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201


def test_analytics_reports_complete_date_range_without_transfers(
    client: TestClient,
) -> None:
    signup(client, "analytics@example.com")
    chequing = client.post(
        "/api/v1/accounts",
        json={"name": "Analytics chequing", "type": "chequing", "currency": "CAD"},
    ).json()
    savings = client.post(
        "/api/v1/accounts",
        json={"name": "Analytics savings", "type": "savings", "currency": "CAD"},
    ).json()
    catalog = client.get("/api/v1/classifications").json()
    essentials = next(item for item in catalog["buckets"] if item["name"] == "Essentials")
    education = next(item for item in catalog["buckets"] if item["name"] == "Education")
    groceries = next(item for item in essentials["categories"] if item["name"] == "Groceries")
    books = next(item for item in education["categories"] if item["name"] == "Books")
    salary = next(item for item in catalog["income_categories"] if item["name"] == "Salary")

    transactions = [
        {
            "type": "income",
            "amount_cad": "2000.00",
            "date": "2026-01-05",
            "description": "January salary",
            "category_id": salary["id"],
        },
        {
            "type": "expense",
            "amount_cad": "300.00",
            "date": "2026-01-10",
            "description": "Groceries",
            "bucket_id": essentials["id"],
            "category_id": groceries["id"],
            "expense_classification": "variable",
            "is_major_purchase": True,
        },
        {
            "type": "expense",
            "amount_cad": "500.00",
            "date": "2026-02-10",
            "description": "Books",
            "bucket_id": education["id"],
            "category_id": books["id"],
            "expense_classification": "fixed",
        },
        {
            "type": "transfer",
            "amount_cad": "1000.00",
            "date": "2026-02-15",
            "description": "Move money",
            "destination_account_id": savings["id"],
        },
    ]
    for item in transactions:
        payload = {"account_id": chequing["id"], **item}
        assert client.post("/api/v1/transactions", json=payload).status_code == 201

    response = client.get(
        "/api/v1/analytics",
        params={"date_from": "2026-01-01", "date_to": "2026-03-31"},
    )
    assert response.status_code == 200
    report = response.json()
    assert report["summary"] == {
        "income_cad": "2000.00",
        "expenses_cad": "800.00",
        "savings_cad": "1200.00",
        "education_spending_cad": "500.00",
        "major_purchase_spending_cad": "300.00",
    }
    assert [(item["name"], item["amount_cad"]) for item in report["spending_by_bucket"]] == [
        ("Education", "500.00"),
        ("Essentials", "300.00"),
    ]
    assert [(item["name"], item["amount_cad"]) for item in report["fixed_vs_variable"]] == [
        ("Fixed", "500.00"),
        ("Variable", "300.00"),
    ]
    assert report["monthly_trend"] == [
        {
            "month": "2026-01",
            "income_cad": "2000.00",
            "expenses_cad": "300.00",
            "savings_cad": "1700.00",
        },
        {
            "month": "2026-02",
            "income_cad": "0.00",
            "expenses_cad": "500.00",
            "savings_cad": "-500.00",
        },
        {"month": "2026-03", "income_cad": "0.00", "expenses_cad": "0.00", "savings_cad": "0.00"},
    ]
    assert [item["description"] for item in report["major_purchases"]] == ["Groceries"]

    assert (
        client.get(
            "/api/v1/analytics",
            params={"date_from": "2026-04-01", "date_to": "2026-03-01"},
        ).status_code
        == 422
    )

    client.cookies.clear()
    signup(client, "empty-analytics@example.com")
    empty = client.get(
        "/api/v1/analytics",
        params={"date_from": "2026-01-01", "date_to": "2026-01-31"},
    ).json()
    assert empty["summary"]["expenses_cad"] == "0.00"
    assert empty["spending_by_bucket"] == []
