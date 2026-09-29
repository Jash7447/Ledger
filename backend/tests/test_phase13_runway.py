from datetime import date

from fastapi.testclient import TestClient


def signup(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "display_name": "Runway User",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    cookie = client.cookies.get("ledger_session")
    assert cookie is not None
    return cookie


def month_start_before(months: int) -> date:
    today = date.today()
    index = today.year * 12 + today.month - 1 - months
    year, month = divmod(index, 12)
    return date(year, month + 1, 1)


def test_runway_uses_configurable_completed_months_and_is_an_estimate(
    client: TestClient,
) -> None:
    first_cookie = signup(client, "runway@example.com")
    account = client.post(
        "/api/v1/accounts",
        json={"name": "Runway account", "type": "chequing", "currency": "CAD"},
    ).json()
    income_date = month_start_before(3).isoformat()
    assert client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "type": "income",
            "amount_cad": "4000.00",
            "date": income_date,
            "description": "Available funds",
        },
    ).status_code == 201
    for months, amount in ((3, "300.00"), (2, "600.00"), (1, "900.00")):
        assert client.post(
            "/api/v1/transactions",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount_cad": amount,
                "date": month_start_before(months).isoformat(),
                "description": f"Expense {months}",
            },
        ).status_code == 201

    defaults = client.get("/api/v1/settings/runway").json()
    assert defaults["is_enabled"] is True
    assert defaults["lookback_months"] == 3
    estimate = client.get("/api/v1/dashboard").json()["runway"]
    assert estimate["available_funds_cad"] == "2200.00"
    assert estimate["average_monthly_spending_cad"] == "600.00"
    assert estimate["estimated_months"] == "3.7"

    assert client.patch(
        "/api/v1/settings/runway", json={"lookback_months": 2}
    ).status_code == 200
    two_month = client.get("/api/v1/dashboard").json()["runway"]
    assert two_month["average_monthly_spending_cad"] == "750.00"
    assert two_month["estimated_months"] == "2.9"

    assert client.patch(
        "/api/v1/settings/runway", json={"is_enabled": False}
    ).status_code == 200
    disabled = client.get("/api/v1/dashboard").json()["runway"]
    assert disabled["estimated_months"] is None
    assert client.patch(
        "/api/v1/settings/runway", json={"lookback_months": 0}
    ).status_code == 422

    client.cookies.clear()
    signup(client, "other-runway@example.com")
    assert client.get("/api/v1/settings/runway").json()["lookback_months"] == 3
    client.cookies.set("ledger_session", first_cookie)
