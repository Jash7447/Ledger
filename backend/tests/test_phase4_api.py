from typing import Any, cast

from fastapi.testclient import TestClient


def signup(client: TestClient, email: str = "phase4@example.com") -> str:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "display_name": "Phase Four",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    cookie = client.cookies.get("ledger_session")
    assert cookie is not None
    return cookie


def create_account(
    client: TestClient, name: str, account_type: str = "chequing"
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/accounts",
        json={"name": name, "type": account_type, "currency": "CAD"},
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


def test_account_transaction_crud_and_derived_balances(client: TestClient) -> None:
    signup(client)
    catalog_response = client.get("/api/v1/classifications")
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    assert len(catalog["buckets"]) == 7
    assert sum(len(bucket["categories"]) for bucket in catalog["buckets"]) == 41
    assert len(catalog["income_categories"]) == 6
    assert len(catalog["funding_categories"]) == 4

    chequing = create_account(client, "Daily chequing")
    savings = create_account(client, "Emergency savings", "savings")
    salary = next(item for item in catalog["income_categories"] if item["name"] == "Salary")
    essentials = next(item for item in catalog["buckets"] if item["name"] == "Essentials")
    groceries = next(item for item in essentials["categories"] if item["name"] == "Groceries")

    income = client.post(
        "/api/v1/transactions",
        json={
            "account_id": chequing["id"],
            "type": "income",
            "amount_cad": "1000.00",
            "date": "2026-09-01",
            "description": "Payday",
            "category_id": salary["id"],
        },
    )
    assert income.status_code == 201

    expense = client.post(
        "/api/v1/transactions",
        json={
            "account_id": chequing["id"],
            "type": "expense",
            "amount_cad": "100.00",
            "date": "2026-09-02",
            "description": "Groceries",
            "bucket_id": essentials["id"],
            "category_id": groceries["id"],
            "expense_classification": "variable",
            "is_major_purchase": False,
        },
    )
    assert expense.status_code == 201
    expense_id = expense.json()["id"]

    transfer = client.post(
        "/api/v1/transactions",
        json={
            "account_id": chequing["id"],
            "destination_account_id": savings["id"],
            "type": "transfer",
            "amount_cad": "250.00",
            "date": "2026-09-03",
            "description": "Move to savings",
        },
    )
    assert transfer.status_code == 201

    accounts = {item["id"]: item for item in client.get("/api/v1/accounts").json()}
    assert accounts[chequing["id"]]["balance_cad"] == "650.00"
    assert accounts[savings["id"]]["balance_cad"] == "250.00"

    detail = client.get(f"/api/v1/transactions/{expense_id}")
    assert detail.status_code == 200
    updated = client.patch(
        f"/api/v1/transactions/{expense_id}",
        json={"amount_cad": "125.50", "notes": "Weekly shop"},
    )
    assert updated.status_code == 200
    assert updated.json()["notes"] == "Weekly shop"
    assert len(client.get("/api/v1/transactions").json()["items"]) == 3

    assert client.delete(f"/api/v1/transactions/{expense_id}").status_code == 204
    assert client.get(f"/api/v1/transactions/{expense_id}").status_code == 404
    chequing_detail = client.get(f"/api/v1/accounts/{chequing['id']}").json()
    assert chequing_detail["balance_cad"] == "750.00"

    renamed = client.patch(
        f"/api/v1/accounts/{savings['id']}", json={"name": "Rainy day"}
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Rainy day"
    assert client.post(f"/api/v1/accounts/{savings['id']}/archive").status_code == 204
    assert len(client.get("/api/v1/accounts").json()) == 1
    archived = client.get("/api/v1/accounts?include_archived=true").json()
    assert len(archived) == 2
    assert next(item for item in archived if item["id"] == savings["id"])["is_active"] is False

    rejected = client.post(
        "/api/v1/transactions",
        json={
            "account_id": savings["id"],
            "type": "income",
            "amount_cad": "20.00",
            "date": "2026-09-04",
            "description": "Invalid archived account entry",
        },
    )
    assert rejected.status_code == 422


def test_financial_resources_are_isolated_by_user(client: TestClient) -> None:
    first_cookie = signup(client, "first-phase4@example.com")
    first_account = create_account(client, "Private account")
    transaction = client.post(
        "/api/v1/transactions",
        json={
            "account_id": first_account["id"],
            "type": "income",
            "amount_cad": "50.00",
            "date": "2026-09-01",
            "description": "Private income",
        },
    ).json()

    client.cookies.clear()
    signup(client, "second-phase4@example.com")
    assert client.get(f"/api/v1/accounts/{first_account['id']}").status_code == 404
    assert client.get(f"/api/v1/transactions/{transaction['id']}").status_code == 404
    account_update = client.patch(
        f"/api/v1/accounts/{first_account['id']}", json={"name": "Mine"}
    )
    assert account_update.status_code == 404
    assert client.delete(f"/api/v1/transactions/{transaction['id']}").status_code == 404

    client.cookies.set("ledger_session", first_cookie)
    assert client.get(f"/api/v1/accounts/{first_account['id']}").status_code == 200
