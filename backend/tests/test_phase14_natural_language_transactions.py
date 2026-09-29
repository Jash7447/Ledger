from datetime import date, timedelta

from fastapi.testclient import TestClient


def signup(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "display_name": "Natural Language User",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    cookie = client.cookies.get("ledger_session")
    assert cookie is not None
    return cookie


def test_natural_language_proposal_requires_preview_and_confirmation(
    client: TestClient,
) -> None:
    signup(client, "natural-entry@example.com")
    account = client.post(
        "/api/v1/accounts",
        json={"name": "Daily chequing", "type": "chequing", "currency": "CAD"},
    ).json()
    proposal_response = client.post(
        "/api/v1/natural-language/transactions/propose",
        json={"text": "Spent $42.50 on dinner with friends yesterday."},
    )
    assert proposal_response.status_code == 200
    proposal = proposal_response.json()
    assert proposal["ready_to_confirm"] is True
    assert proposal["type"] == "expense"
    assert proposal["amount_cad"] == "42.50"
    assert proposal["date"] == (date.today() - timedelta(days=1)).isoformat()
    assert proposal["account_id"] == account["id"]
    assert proposal["bucket_name"] == "Leisure"
    assert proposal["category_name"] == "Restaurants"
    assert client.get("/api/v1/transactions").json()["total"] == 0

    transaction = {
        "account_id": proposal["account_id"],
        "type": proposal["type"],
        "amount_cad": proposal["amount_cad"],
        "date": proposal["date"],
        "description": "Dinner with friends",
        "bucket_id": proposal["bucket_id"],
        "category_id": proposal["category_id"],
        "is_major_purchase": proposal["is_major_purchase"],
    }
    confirmed = client.post(
        "/api/v1/natural-language/transactions/confirm",
        json={"source_text": proposal["source_text"], "transaction": transaction},
    )
    assert confirmed.status_code == 201
    assert confirmed.json()["description"] == "Dinner with friends"
    assert client.get("/api/v1/transactions").json()["total"] == 1


def test_natural_language_income_validation_and_ownership(client: TestClient) -> None:
    first_cookie = signup(client, "natural-income@example.com")
    account = client.post(
        "/api/v1/accounts",
        json={"name": "Income account", "type": "chequing", "currency": "CAD"},
    ).json()
    proposal = client.post(
        "/api/v1/natural-language/transactions/propose",
        json={"text": "Received CAD 1000 salary today"},
    ).json()
    assert proposal["type"] == "income"
    assert proposal["category_name"] == "Salary"
    assert proposal["bucket_id"] is None

    incomplete = client.post(
        "/api/v1/natural-language/transactions/propose",
        json={"text": "Something happened yesterday"},
    ).json()
    assert incomplete["ready_to_confirm"] is False
    assert len(incomplete["errors"]) == 2
    assert client.get("/api/v1/transactions").json()["total"] == 0

    client.cookies.clear()
    signup(client, "other-natural@example.com")
    foreign_confirm = client.post(
        "/api/v1/natural-language/transactions/confirm",
        json={
            "source_text": "Spent $10 today",
            "transaction": {
                "account_id": account["id"],
                "type": "expense",
                "amount_cad": "10.00",
                "date": date.today().isoformat(),
                "description": "Not my account",
            },
        },
    )
    assert foreign_confirm.status_code == 422
    client.cookies.set("ledger_session", first_cookie)
