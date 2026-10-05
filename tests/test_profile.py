"""Tests for user profile view, editing details, and changing password."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from autodrop.core.security import verify_password
from autodrop.models.user import User


def test_view_profile_requires_auth(client: TestClient):
    """Verifies that accessing /profile unauthenticated redirects to login."""
    response = client.get("/profile", headers={"Accept": "text/html"}, follow_redirects=False)
    assert response.status_code == 303
    assert "/auth/login" in response.headers["location"]


def test_view_profile_authenticated(authenticated_client: TestClient, verified_user: User):
    """Verifies that authenticated user can view their profile."""
    response = authenticated_client.get("/profile")
    assert response.status_code == 200
    assert verified_user.email in response.text
    assert verified_user.first_name in response.text


def test_update_profile_success(authenticated_client: TestClient, verified_user: User, db: Session):
    """Verifies updating user profile fields."""
    response = authenticated_client.post(
        "/profile",
        data={
            "first_name": "Johnny",
            "last_name": "Updated",
            "phone": "+36709998888",
        },
    )
    assert response.status_code == 200

    db.refresh(verified_user)
    assert verified_user.first_name == "Johnny"
    assert verified_user.last_name == "Updated"
    assert verified_user.phone == "+36709998888"


def test_change_password_success(authenticated_client: TestClient, verified_user: User, db: Session):
    """Verifies successful password change."""
    response = authenticated_client.post(
        "/profile/change-password",
        data={
            "current_password": "Password123!",
            "new_password": "NewSecretPassword123!",
            "confirm_password": "NewSecretPassword123!",
        },
    )
    assert response.status_code == 200
    assert "sikeresen" in response.text.lower() or "successfully" in response.text.lower()

    db.refresh(verified_user)
    assert verify_password("NewSecretPassword123!", verified_user.hashed_password)


def test_change_password_wrong_current(authenticated_client: TestClient):
    """Verifies that providing incorrect current password fails."""
    response = authenticated_client.post(
        "/profile/change-password",
        data={
            "current_password": "WrongCurrentPassword!",
            "new_password": "NewSecretPassword123!",
            "confirm_password": "NewSecretPassword123!",
        },
    )
    assert response.status_code == 400
