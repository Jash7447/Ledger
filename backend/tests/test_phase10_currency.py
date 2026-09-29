from fastapi.testclient import TestClient


def signup(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "display_name": "Currency User",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    cookie = client.cookies.get("ledger_session")
    assert cookie is not None
    return cookie


def test_currency_settings_are_owned_and_do_not_duplicate_financial_values(
    client: TestClient,
) -> None:
    first_cookie = signup(client, "currency@example.com")
    defaults = client.get("/api/v1/settings/currency")
    assert defaults.status_code == 200
    assert defaults.json()["display_currency"] == "CAD"
    assert defaults.json()["cad_to_inr_rate"] == "70.0000"

    updated = client.patch(
        "/api/v1/settings/currency",
        json={"display_currency": "INR", "cad_to_inr_rate": "61.4321"},
    )
    assert updated.status_code == 200
    assert updated.json()["display_currency"] == "INR"
    assert updated.json()["cad_to_inr_rate"] == "61.4321"

    account = client.post(
        "/api/v1/accounts",
        json={"name": "CAD only", "type": "chequing", "currency": "CAD"},
    ).json()
    transaction = client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "type": "income",
            "amount_cad": "100.00",
            "date": "2026-09-28",
            "description": "Canonical CAD",
        },
    ).json()
    assert transaction["amount_cad"] == "100.00"
    assert "amount_inr" not in transaction

    client.cookies.clear()
    signup(client, "other-currency@example.com")
    other = client.get("/api/v1/settings/currency").json()
    assert other["display_currency"] == "CAD"
    assert other["cad_to_inr_rate"] == "70.0000"

    client.cookies.set("ledger_session", first_cookie)
    assert client.patch(
        "/api/v1/settings/currency", json={"cad_to_inr_rate": "0"}
    ).status_code == 422
    assert client.patch(
        "/api/v1/settings/currency", json={"display_currency": "USD"}
    ).status_code == 422
