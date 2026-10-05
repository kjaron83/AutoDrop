"""Tests for admin user directory inspection and management."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from autodrop.models.user import User


def test_admin_users_forbidden_for_regular_user(authenticated_client: TestClient):
    """Verifies that standard non-admin users get 403 Forbidden on /admin/users."""
    response = authenticated_client.get("/admin/users")
    assert response.status_code == 403


def test_admin_users_list(authenticated_admin_client: TestClient, verified_user: User):
    """Verifies that admin can view the user list."""
    response = authenticated_admin_client.get("/admin/users")
    assert response.status_code == 200
    assert verified_user.email in response.text


def test_admin_users_htmx_table_search(authenticated_admin_client: TestClient, verified_user: User):
    """Verifies HTMX table search endpoint."""
    response = authenticated_admin_client.get(f"/admin/users/table?search={verified_user.first_name}")
    assert response.status_code == 200
    assert verified_user.email in response.text


def test_admin_edit_user(authenticated_admin_client: TestClient, verified_user: User, db: Session):
    """Verifies that admin can edit a user's details and flags."""
    response = authenticated_admin_client.post(
        f"/admin/users/{verified_user.id}",
        data={
            "first_name": "Modified",
            "last_name": "Name",
            "phone": "+36201112222",
            "is_admin": "true",
            "is_active": "true",
            "is_verified": "true",
        },
    )
    assert response.status_code == 200

    db.refresh(verified_user)
    assert verified_user.first_name == "Modified"
    assert verified_user.last_name == "Name"
    assert verified_user.is_admin is True


def test_admin_toggle_user_status(authenticated_admin_client: TestClient, verified_user: User, db: Session):
    """Verifies toggling user active status."""
    assert verified_user.is_active is True
    response = authenticated_admin_client.post(
        f"/admin/users/{verified_user.id}/toggle-status",
        follow_redirects=False,
    )
    assert response.status_code == 303

    db.refresh(verified_user)
    assert verified_user.is_active is False
