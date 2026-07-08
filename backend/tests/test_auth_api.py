from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_login_and_read_current_user(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "BHAVANA@example.com",
            "full_name": "Bhavana Hegde",
            "password": "secure-password",
        },
    )

    assert register_response.status_code == 201
    registered_user = register_response.json()
    assert registered_user["email"] == "bhavana@example.com"
    assert registered_user["full_name"] == "Bhavana Hegde"
    assert registered_user["role"] == "viewer"
    assert "hashed_password" not in registered_user

    token_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "bhavana@example.com",
            "password": "secure-password",
        },
    )

    assert token_response.status_code == 200
    token_payload = token_response.json()
    assert token_payload["token_type"] == "bearer"
    assert token_payload["access_token"].count(".") == 2

    current_user_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_payload['access_token']}"},
    )

    assert current_user_response.status_code == 200
    assert current_user_response.json()["email"] == "bhavana@example.com"


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "duplicate@example.com",
        "full_name": "Duplicate User",
        "password": "secure-password",
    }

    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "A user with this email already exists."


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong-password@example.com",
            "full_name": "Wrong Password",
            "password": "secure-password",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong-password@example.com",
            "password": "bad-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_protected_routes_require_bearer_token(client: TestClient) -> None:
    response = client.get("/api/v1/incidents")

    assert response.status_code == 401
