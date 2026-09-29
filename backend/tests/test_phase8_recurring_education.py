from fastapi.testclient import TestClient


def signup(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "display_name": "Phase Eight",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    cookie = client.cookies.get("ledger_session")
    assert cookie is not None
    return cookie


def test_recurring_definitions_are_owned_and_do_not_post_transactions(
    client: TestClient,
) -> None:
    first_cookie = signup(client, "recurring@example.com")
    account = client.post(
        "/api/v1/accounts",
        json={"name": "Bills account", "type": "chequing", "currency": "CAD"},
    ).json()
    catalog = client.get("/api/v1/classifications").json()
    essentials = next(item for item in catalog["buckets"] if item["name"] == "Essentials")
    rent = next(item for item in essentials["categories"] if item["name"] == "Rent")

    response = client.post(
        "/api/v1/recurring",
        json={
            "account_id": account["id"],
            "category_id": rent["id"],
            "description": "Monthly rent",
            "expected_amount_cad": "850.00",
            "frequency": "monthly",
            "start_date": "2099-01-31",
            "end_date": "2099-12-31",
            "notes": "Expected only",
        },
    )
    assert response.status_code == 201
    recurring = response.json()
    assert recurring["bucket_name"] == "Essentials"
    assert recurring["category_name"] == "Rent"
    assert recurring["account_name"] == "Bills account"
    assert recurring["next_occurrence_date"] == "2099-01-31"
    assert recurring["is_active"] is True

    transactions = client.get("/api/v1/transactions").json()
    assert transactions["total"] == 0
    assert client.get(f"/api/v1/accounts/{account['id']}").json()["balance_cad"] == "0.00"

    listed = client.get("/api/v1/recurring", params={"is_active": True}).json()
    assert [item["id"] for item in listed] == [recurring["id"]]
    updated = client.patch(
        f"/api/v1/recurring/{recurring['id']}",
        json={"expected_amount_cad": "900.00", "is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["expected_amount_cad"] == "900.00"
    assert updated.json()["next_occurrence_date"] is None
    assert client.get("/api/v1/recurring", params={"is_active": True}).json() == []

    client.cookies.clear()
    signup(client, "other-recurring@example.com")
    assert client.get(f"/api/v1/recurring/{recurring['id']}").status_code == 404
    foreign = client.post(
        "/api/v1/recurring",
        json={
            "account_id": account["id"],
            "category_id": rent["id"],
            "description": "Not mine",
            "expected_amount_cad": "10.00",
            "frequency": "weekly",
            "start_date": "2030-01-01",
        },
    )
    assert foreign.status_code == 422

    client.cookies.set("ledger_session", first_cookie)
    assert client.delete(f"/api/v1/recurring/{recurring['id']}").status_code == 204
    assert client.get(f"/api/v1/recurring/{recurring['id']}").status_code == 404


def test_recurring_validation_and_education_reporting(client: TestClient) -> None:
    signup(client, "education@example.com")
    account = client.post(
        "/api/v1/accounts",
        json={"name": "Student account", "type": "chequing", "currency": "CAD"},
    ).json()
    catalog = client.get("/api/v1/classifications").json()
    education = next(item for item in catalog["buckets"] if item["name"] == "Education")
    essentials = next(item for item in catalog["buckets"] if item["name"] == "Essentials")
    expected_categories = {
        "Tuition",
        "Student Fees",
        "Health Fees",
        "Books",
        "Course Materials",
        "Software",
        "Exams",
        "Certifications",
        "Other Education",
    }
    assert {item["name"] for item in education["categories"]} == expected_categories
    tuition = next(item for item in education["categories"] if item["name"] == "Tuition")
    books = next(item for item in education["categories"] if item["name"] == "Books")
    rent = next(item for item in essentials["categories"] if item["name"] == "Rent")
    salary = next(item for item in catalog["income_categories"] if item["name"] == "Salary")

    invalid_dates = client.post(
        "/api/v1/recurring",
        json={
            "account_id": account["id"],
            "category_id": rent["id"],
            "description": "Invalid dates",
            "expected_amount_cad": "10.00",
            "frequency": "monthly",
            "start_date": "2030-02-01",
            "end_date": "2030-01-01",
        },
    )
    assert invalid_dates.status_code == 422
    invalid_category = client.post(
        "/api/v1/recurring",
        json={
            "account_id": account["id"],
            "category_id": salary["id"],
            "description": "Invalid category",
            "expected_amount_cad": "10.00",
            "frequency": "monthly",
            "start_date": "2030-01-01",
        },
    )
    assert invalid_category.status_code == 422

    for amount, transaction_date, description, category in (
        ("1000.00", "2026-09-01", "Fall tuition", tuition),
        ("120.00", "2026-09-10", "Course books", books),
        ("80.00", "2026-08-01", "Earlier books", books),
    ):
        assert client.post(
            "/api/v1/transactions",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount_cad": amount,
                "date": transaction_date,
                "description": description,
                "bucket_id": education["id"],
                "category_id": category["id"],
            },
        ).status_code == 201
    assert client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "type": "expense",
            "amount_cad": "500.00",
            "date": "2026-09-02",
            "description": "Rent is not education",
            "bucket_id": essentials["id"],
            "category_id": rent["id"],
        },
    ).status_code == 201

    report = client.get(
        "/api/v1/education",
        params={"date_from": "2026-09-01", "date_to": "2026-09-30"},
    )
    assert report.status_code == 200
    payload = report.json()
    assert payload["total_spent_cad"] == "1120.00"
    assert payload["transaction_count"] == 2
    assert [item["category_name"] for item in payload["spending_by_category"]] == [
        "Tuition",
        "Books",
    ]
    assert [item["description"] for item in payload["transactions"]] == [
        "Course books",
        "Fall tuition",
    ]
    assert client.get(
        "/api/v1/education",
        params={"date_from": "2026-10-01", "date_to": "2026-09-01"},
    ).status_code == 422
