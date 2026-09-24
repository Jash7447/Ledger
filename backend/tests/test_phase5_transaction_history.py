from typing import Any, cast

from fastapi.testclient import TestClient


def setup_history(client: TestClient) -> dict[str, Any]:
    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "history@example.com",
            "display_name": "History User",
            "password": "correct-horse-battery-staple",
        },
    )
    assert signup.status_code == 201
    account = client.post(
        "/api/v1/accounts",
        json={"name": "History chequing", "type": "chequing", "currency": "CAD"},
    ).json()
    savings = client.post(
        "/api/v1/accounts",
        json={"name": "History savings", "type": "savings", "currency": "CAD"},
    ).json()
    catalog = client.get("/api/v1/classifications").json()
    essentials = next(item for item in catalog["buckets"] if item["name"] == "Essentials")
    leisure = next(item for item in catalog["buckets"] if item["name"] == "Leisure")
    groceries = next(item for item in essentials["categories"] if item["name"] == "Groceries")
    coffee = next(item for item in leisure["categories"] if item["name"] == "Coffee")
    salary = next(item for item in catalog["income_categories"] if item["name"] == "Salary")

    transactions = [
        {
            "account_id": account["id"],
            "type": "income",
            "amount_cad": "2000.00",
            "date": "2026-01-01",
            "description": "January salary",
            "category_id": salary["id"],
            "notes": "Monthly payroll",
        },
        {
            "account_id": account["id"],
            "type": "expense",
            "amount_cad": "80.00",
            "date": "2026-01-04",
            "description": "Grocery market",
            "bucket_id": essentials["id"],
            "category_id": groceries["id"],
            "expense_classification": "variable",
            "is_major_purchase": False,
        },
        {
            "account_id": account["id"],
            "type": "expense",
            "amount_cad": "180.00",
            "date": "2026-02-02",
            "description": "Coffee machine",
            "bucket_id": leisure["id"],
            "category_id": coffee["id"],
            "expense_classification": "variable",
            "is_major_purchase": True,
            "notes": "Kitchen upgrade",
        },
        {
            "account_id": account["id"],
            "destination_account_id": savings["id"],
            "type": "transfer",
            "amount_cad": "500.00",
            "date": "2026-02-03",
            "description": "Emergency fund transfer",
        },
    ]
    for transaction in transactions:
        assert client.post("/api/v1/transactions", json=transaction).status_code == 201
    return cast(
        dict[str, Any],
        {
            "account": account,
            "savings": savings,
            "essentials": essentials,
            "leisure": leisure,
            "groceries": groceries,
            "coffee": coffee,
        },
    )


def test_transaction_history_search_filters_and_sorting(client: TestClient) -> None:
    data = setup_history(client)

    search = client.get("/api/v1/transactions", params={"search": "kitchen"}).json()
    assert search["total"] == 1
    assert search["items"][0]["description"] == "Coffee machine"

    date_range = client.get(
        "/api/v1/transactions",
        params={"date_from": "2026-01-02", "date_to": "2026-02-02"},
    ).json()
    assert date_range["total"] == 2

    by_account = client.get(
        "/api/v1/transactions", params={"account_id": data["savings"]["id"]}
    ).json()
    assert by_account["total"] == 1
    assert by_account["items"][0]["type"] == "transfer"

    by_bucket = client.get(
        "/api/v1/transactions", params={"bucket_id": data["essentials"]["id"]}
    ).json()
    assert [item["description"] for item in by_bucket["items"]] == ["Grocery market"]

    by_category = client.get(
        "/api/v1/transactions", params={"category_id": data["coffee"]["id"]}
    ).json()
    assert by_category["total"] == 1

    major = client.get(
        "/api/v1/transactions", params={"is_major_purchase": True}
    ).json()
    assert major["total"] == 1
    assert major["items"][0]["is_major_purchase"] is True

    expenses = client.get(
        "/api/v1/transactions",
        params={"type": "expense", "sort_by": "amount", "sort_direction": "asc"},
    ).json()
    assert expenses["total"] == 2
    assert [item["amount_cad"] for item in expenses["items"]] == ["80.00", "180.00"]

    invalid_range = client.get(
        "/api/v1/transactions",
        params={"date_from": "2026-03-01", "date_to": "2026-02-01"},
    )
    assert invalid_range.status_code == 422


def test_transaction_history_pagination_and_literal_search(client: TestClient) -> None:
    setup_history(client)
    first_page = client.get(
        "/api/v1/transactions",
        params={"page": 1, "page_size": 2, "sort_by": "date", "sort_direction": "asc"},
    ).json()
    second_page = client.get(
        "/api/v1/transactions",
        params={"page": 2, "page_size": 2, "sort_by": "date", "sort_direction": "asc"},
    ).json()
    assert first_page["total"] == 4
    assert first_page["pages"] == 2
    assert first_page["page"] == 1
    assert len(first_page["items"]) == 2
    assert first_page["items"][0]["description"] == "January salary"
    assert second_page["items"][0]["description"] == "Coffee machine"

    literal_wildcard = client.get("/api/v1/transactions", params={"search": "%"}).json()
    assert literal_wildcard["total"] == 0
