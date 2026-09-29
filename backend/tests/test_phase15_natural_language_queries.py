from datetime import date

from fastapi.testclient import TestClient


def signup(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "display_name": "Query User",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    cookie = client.cookies.get("ledger_session")
    assert cookie is not None
    return cookie


def test_read_queries_use_controlled_owned_financial_data(client: TestClient) -> None:
    first_cookie = signup(client, "queries@example.com")
    account = client.post(
        "/api/v1/accounts",
        json={"name": "Query account", "type": "chequing", "currency": "CAD"},
    ).json()
    catalog = client.get("/api/v1/classifications").json()
    essentials = next(item for item in catalog["buckets"] if item["name"] == "Essentials")
    education = next(item for item in catalog["buckets"] if item["name"] == "Education")
    groceries = next(item for item in essentials["categories"] if item["name"] == "Groceries")
    tuition = next(item for item in education["categories"] if item["name"] == "Tuition")
    today = date.today().isoformat()
    for description, amount, bucket, category, major in (
        ("Groceries", "120.00", essentials, groceries, False),
        ("Tuition", "900.00", education, tuition, True),
    ):
        assert client.post(
            "/api/v1/transactions",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount_cad": amount,
                "date": today,
                "description": description,
                "bucket_id": bucket["id"],
                "category_id": category["id"],
                "is_major_purchase": major,
            },
        ).status_code == 201
    alex = client.post("/api/v1/people", json={"name": "Alex"}).json()
    assert client.post(
        f"/api/v1/people/{alex['id']}/events",
        json={
            "event_type": "borrowed",
            "amount_cad": "80.00",
            "date": today,
        },
    ).status_code == 201

    spending = client.post(
        "/api/v1/natural-language/query",
        json={"question": "How much did I spend this month?"},
    ).json()
    assert spending["intent"] == "spending_total"
    assert spending["amount_cad"] == "1020.00"
    assert spending["count"] == 2
    food = client.post(
        "/api/v1/natural-language/query",
        json={"question": "How much did I spend on food?"},
    ).json()
    assert food["amount_cad"] == "120.00"
    tuition_result = client.post(
        "/api/v1/natural-language/query",
        json={"question": "How much did I spend on tuition?"},
    ).json()
    assert tuition_result["amount_cad"] == "900.00"
    biggest = client.post(
        "/api/v1/natural-language/query",
        json={"question": "What were my biggest purchases?"},
    ).json()
    assert biggest["count"] == 1
    assert biggest["structured_data"]["purchases"][0]["description"] == "Tuition"
    owed = client.post(
        "/api/v1/natural-language/query",
        json={"question": "How much do I owe Alex?"},
    ).json()
    assert owed["amount_cad"] == "80.00"
    assert client.get("/api/v1/transactions").json()["total"] == 2

    client.cookies.clear()
    signup(client, "other-queries@example.com")
    isolated = client.post(
        "/api/v1/natural-language/query",
        json={"question": "How much did I spend this month?"},
    ).json()
    assert isolated["amount_cad"] == "0.00"
    missing_person = client.post(
        "/api/v1/natural-language/query",
        json={"question": "How much do I owe Alex?"},
    ).json()
    assert missing_person["structured_data"]["person_found"] is False
    client.cookies.set("ledger_session", first_cookie)


def test_unsupported_query_is_safe_and_read_only(client: TestClient) -> None:
    signup(client, "unsupported-query@example.com")
    response = client.post(
        "/api/v1/natural-language/query",
        json={"question": "Which stock should I buy?"},
    )
    assert response.status_code == 200
    assert response.json()["intent"] == "unsupported"
