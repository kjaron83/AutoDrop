"""Tests for user registration, verification, login, logout, and password resets."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from autodrop.core.config import settings
from autodrop.core.security import verify_password
from autodrop.models.user import EmailVerificationToken, PasswordResetToken, User
from autodrop.services.email import test_outbox


def test_registration_success(client: TestClient, db: Session):
    """Verifies that registration creates unverified user and sends verification email."""
    response = client.post(
        "/auth/register",
        data={
            "first_name": "Peter",
            "last_name": "Kovacs",
            "email": "peter@example.com",
            "password": "SecurePassword123!",
            "phone": "+36301234567",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "/auth/verify-notice" in response.headers["location"]

    user = db.query(User).filter_by(email="peter@example.com").first()
    assert user is not None
    assert user.first_name == "Peter"
    assert user.last_name == "Kovacs"
    assert user.is_verified is False
    assert user.is_active is True
    assert user.is_admin is False
    assert user.phone == "+36301234567"

    token = db.query(EmailVerificationToken).filter_by(user_id=user.id).first()
    assert token is not None
    assert token.is_used is False

    # Check test email was dispatched
    assert len(test_outbox) == 1
    assert test_outbox[0]["to"] == "peter@example.com"
    assert token.token in test_outbox[0]["html"]


def test_registration_duplicate_email(client: TestClient, verified_user: User):
    """Verifies that registration with existing email fails."""
    response = client.post(
        "/auth/register",
        data={
            "first_name": "Another",
            "last_name": "User",
            "email": verified_user.email,
            "password": "NewPassword123!",
        },
    )
    assert response.status_code == 400


def test_registration_short_password(client: TestClient):
    """Verifies that registration rejects passwords shorter than 8 characters."""
    response = client.post(
        "/auth/register",
        data={
            "first_name": "Short",
            "last_name": "Pass",
            "email": "short@example.com",
            "password": "short",
        },
    )
    assert response.status_code == 400


def test_email_verification_success(client: TestClient, db: Session):
    """Verifies that clicking valid verification link activates the user."""
    # Register first
    client.post(
        "/auth/register",
        data={
            "first_name": "Eva",
            "last_name": "Nagy",
            "email": "eva@example.com",
            "password": "Password123!",
        },
    )
    user = db.query(User).filter_by(email="eva@example.com").first()
    token = db.query(EmailVerificationToken).filter_by(user_id=user.id).first()

    # Verify link
    response = client.get(f"/auth/verify-email?token={token.token}")
    assert response.status_code == 200

    db.refresh(user)
    db.refresh(token)
    assert user.is_verified is True
    assert token.is_used is True


def test_email_verification_invalid_token(client: TestClient):
    """Verifies that invalid verification token returns error."""
    response = client.get("/auth/verify-email?token=non-existent-token")
    assert response.status_code == 400


def test_login_unverified_account_fails(client: TestClient, db: Session):
    """Verifies that unverified user cannot log in."""
    client.post(
        "/auth/register",
        data={
            "first_name": "Pending",
            "last_name": "User",
            "email": "pending@example.com",
            "password": "Password123!",
        },
    )

    response = client.post(
        "/auth/login",
        data={"email": "pending@example.com", "password": "Password123!"},
    )
    assert response.status_code == 400


def test_login_deactivated_account_fails(client: TestClient, db: Session, verified_user: User):
    """Verifies that deactivated account cannot log in."""
    verified_user.is_active = False
    db.commit()

    response = client.post(
        "/auth/login",
        data={"email": verified_user.email, "password": "Password123!"},
    )
    assert response.status_code == 400


def test_login_wrong_password_fails(client: TestClient, verified_user: User):
    """Verifies that wrong password fails login."""
    response = client.post(
        "/auth/login",
        data={"email": verified_user.email, "password": "WrongPassword!"},
    )
    assert response.status_code == 400


def test_login_and_logout_success(client: TestClient, verified_user: User):
    """Verifies successful login sets cookie, redirects to home '/', and logout clears cookie."""
    response = client.post(
        "/auth/login",
        data={"email": verified_user.email, "password": "Password123!"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert settings.SESSION_COOKIE_NAME in response.cookies

    # Logout
    logout_res = client.post("/auth/logout", follow_redirects=False)
    assert logout_res.status_code == 303
    assert logout_res.headers["location"] == "/auth/login"


def test_login_with_next_param(client: TestClient, verified_user: User):
    """Verifies that login with a valid next parameter redirects to that path."""
    response = client.post(
        "/auth/login",
        data={"email": verified_user.email, "password": "Password123!", "next": "/admin/users"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/users"


def test_authenticated_user_auth_pages_redirect_to_home(client: TestClient, verified_user: User):
    """Verifies that authenticated users visiting /auth/login or /auth/register are redirected to '/'."""
    # Log in first
    client.post(
        "/auth/login",
        data={"email": verified_user.email, "password": "Password123!"},
    )

    login_res = client.get("/auth/login", follow_redirects=False)
    assert login_res.status_code == 303
    assert login_res.headers["location"] == "/"

    register_res = client.get("/auth/register", follow_redirects=False)
    assert register_res.status_code == 303
    assert register_res.headers["location"] == "/"


def test_password_reset_flow(client: TestClient, db: Session, verified_user: User):
    """Verifies forgot password token generation and password reset completion."""
    # Request reset
    response = client.post(
        "/auth/forgot-password",
        data={"email": verified_user.email},
    )
    assert response.status_code == 200

    token = db.query(PasswordResetToken).filter_by(user_id=verified_user.id, is_used=False).first()
    assert token is not None

    # Reset password with token
    reset_res = client.post(
        "/auth/reset-password",
        data={
            "token": token.token,
            "password": "BrandNewPassword123!",
            "confirm_password": "BrandNewPassword123!",
        },
    )
    assert reset_res.status_code == 200

    db.refresh(verified_user)
    assert verify_password("BrandNewPassword123!", verified_user.hashed_password)


def test_email_from_and_reply_to_headers(monkeypatch):
    """Verifies that send_email formats From header with APP_NAME and Reply-To with APP_EMAIL."""
    from autodrop.services.email import clear_test_outbox, send_email, test_outbox

    clear_test_outbox()
    monkeypatch.setattr(settings, "APP_NAME", "AutoDrop Store")
    monkeypatch.setattr(settings, "SMTP_FROM", "noreply@autodrop.local")
    monkeypatch.setattr(settings, "APP_EMAIL", "info@autodrop.local")

    send_email("member@example.com", "Test Subject", "<p>Hello</p>")

    assert len(test_outbox) == 1
    assert test_outbox[0]["from"] == "AutoDrop Store <noreply@autodrop.local>"
    assert test_outbox[0]["reply_to"] == "AutoDrop Store <info@autodrop.local>"
