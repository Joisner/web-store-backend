import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from httpx import Response # For type hinting response

from app.core.config import settings
from app import schemas # Import top-level schemas
from app.services import user_service # Import user_service instance

# --- Test User Registration ---

def test_register_new_user(client: TestClient, db: Session, faker_instance):
    email = faker_instance.email()
    password = faker_instance.password(length=12)
    name = faker_instance.name()

    response: Response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": email, "password": password, "name": name, "role": "Usuario", "status": "active"},
    )
    assert response.status_code == 200 # Or 201 if you change it in the endpoint
    data = response.json()
    assert data["email"] == email
    assert data["name"] == name
    assert "id" in data
    assert "hashed_password" not in data # Ensure hashed_password is not returned

    # Verify user is in DB
    user_in_db = user_service.get_by_email(db, email=email)
    assert user_in_db is not None
    assert user_in_db.name == name

def test_register_existing_user_email(client: TestClient, test_user_data: dict): # Uses test_user from conftest
    # First user is created by test_user fixture (implicitly via test_user_data being used by other fixtures)
    # Attempt to register again with the same email
    response: Response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": test_user_data["email"], "password": "anotherpassword", "name": "Another Name"},
    )
    assert response.status_code == 400 # Or the specific code used in your service/endpoint
    data = response.json()
    assert "detail" in data
    # Check if detail message is as expected, e.g. "The user with this email already exists..."


# --- Test User Login ---

def test_login_access_token(client: TestClient, test_user, test_user_data: dict): # test_user fixture ensures user exists
    login_data = {"username": test_user_data["email"], "password": test_user_data["password"]}
    response: Response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)

    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"
    assert "refresh_token" in tokens

def test_login_wrong_password(client: TestClient, test_user_data: dict):
    login_data = {"username": test_user_data["email"], "password": "wrongpassword"}
    response: Response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    assert response.status_code == 401 # As per endpoint definition
    data = response.json()
    assert data["detail"] == "Incorrect email or password"

def test_login_non_existent_user(client: TestClient, faker_instance):
    email = faker_instance.email()
    password = faker_instance.password()
    login_data = {"username": email, "password": password}
    response: Response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Incorrect email or password"


# --- Test Get Current User (/me) ---

def test_read_current_user(client: TestClient, auth_headers: dict, test_user_data: dict):
    response: Response = client.get(f"{settings.API_V1_STR}/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["name"] == test_user_data["name"]
    assert "id" in data

def test_read_current_user_no_token(client: TestClient):
    response: Response = client.get(f"{settings.API_V1_STR}/auth/me")
    assert response.status_code == 401 # FastAPI's default for missing OAuth2 token
    # The detail might vary based on FastAPI version or if you customize it
    # Example: assert response.json()["detail"] == "Not authenticated"

def test_read_current_user_invalid_token(client: TestClient):
    headers = {"Authorization": "Bearer invalidtoken"}
    response: Response = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
    assert response.status_code == 403 # As per get_current_user_token dependency
    assert response.json()["detail"] == "Could not validate credentials"


# --- Test Refresh Token ---
def test_refresh_token(client: TestClient, db: Session, test_user_data: dict):
    # 1. Login to get initial tokens
    login_resp: Response = client.post(
        f"{settings.API_V1_STR}/auth/login/access-token",
        data={"username": test_user_data["email"], "password": test_user_data["password"]},
    )
    assert login_resp.status_code == 200
    initial_tokens = login_resp.json()
    refresh_token = initial_tokens.get("refresh_token")
    assert refresh_token is not None

    # 2. Use refresh token to get new access token
    refresh_resp: Response = client.post(
        f"{settings.API_V1_STR}/auth/token/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert new_tokens["token_type"] == "bearer"
    assert "refresh_token" not in new_tokens # Endpoint currently doesn't re-issue refresh token

    # 3. Verify new access token works
    headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
    me_resp: Response = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == test_user_data["email"]


def test_refresh_token_invalid(client: TestClient):
    response: Response = client.post(
        f"{settings.API_V1_STR}/auth/token/refresh",
        json={"refresh_token": "this.is.an.invalid.token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"

# TODO: Add test for inactive user trying to login (if status check is strictly enforced at login)
# TODO: Add test for inactive user trying to refresh token (if status check is strictly enforced at refresh)
# TODO: Test token expiry if possible (might require mocking time or short-lived tokens in test settings)
