from fastapi.testclient import TestClient


def signup(client: TestClient, email: str = "alex@example.com") -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "display_name": "Alex",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_authentication_lifecycle(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401

    payload = signup(client, "Alex@Example.com")
    assert payload["user"]["email"] == "alex@example.com"
    assert "password" not in payload["user"]
    assert client.cookies.get("ledger_session") is not None

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["id"] == payload["user"]["id"]

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "alex@example.com", "password": "correct-horse-battery-staple"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["user"]["id"] == payload["user"]["id"]


def test_duplicate_email_and_invalid_credentials(client: TestClient) -> None:
    signup(client)
    duplicate = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "ALEX@example.com",
            "display_name": "Another Alex",
            "password": "another-secure-password",
        },
    )
    assert duplicate.status_code == 409

    invalid_login = client.post(
        "/api/v1/auth/login",
        json={"email": "alex@example.com", "password": "wrong-password"},
    )
    assert invalid_login.status_code == 401
    assert invalid_login.json() == {"detail": "Incorrect email or password"}


def test_sessions_resolve_each_users_own_identity(client: TestClient) -> None:
    first_user = signup(client, "first@example.com")["user"]
    first_cookie = client.cookies.get("ledger_session")

    client.cookies.clear()
    second_user = signup(client, "second@example.com")["user"]
    second_cookie = client.cookies.get("ledger_session")

    client.cookies.set("ledger_session", first_cookie)
    first_response = client.get("/api/v1/auth/me")
    client.cookies.set("ledger_session", second_cookie)
    second_response = client.get("/api/v1/auth/me")

    assert first_response.json()["id"] == first_user["id"]
    assert second_response.json()["id"] == second_user["id"]
    assert first_response.json()["id"] != second_response.json()["id"]
