"""Authentication service handling registration, verification, login, and password resets."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from autodrop.core.config import settings
from autodrop.core.i18n import _
from autodrop.core.security import generate_secure_token, hash_password, verify_password
from autodrop.models.user import EmailVerificationToken, PasswordResetToken, User
from autodrop.services.email import send_password_reset_email, send_verification_email
from autodrop.services.user import get_user_by_email


def register_user(
    db: Session,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    phone: Optional[str] = None,
    base_url: str = "",
) -> Tuple[Optional[User], str]:
    """Registers a new user in unverified state and dispatches verification email.

    Args:
        db: Database session.
        email: User email address.
        password: User plain password.
        first_name: First name.
        last_name: Last name.
        phone: Optional phone.
        base_url: Application base URL for verification link.

    Returns:
        Tuple of (User, success_or_error_message).
    """
    clean_email = email.strip().lower()
    existing = get_user_by_email(db, clean_email)
    if existing:
        return None, _("An account with this email address already exists.")

    user = User(
        email=clean_email,
        hashed_password=hash_password(password),
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        phone=phone.strip() if phone else None,
        is_active=True,
        is_verified=False,
        is_admin=False,
    )
    db.add(user)
    db.flush()

    token = create_email_verification_token(db, user)
    db.commit()
    db.refresh(user)

    # Send verification email
    verify_url = f"{base_url.rstrip('/')}/auth/verify-email?token={token.token}"
    send_verification_email(user.email, user.first_name, verify_url)

    return user, _("Registration successful! Please check your email to verify your account.")


def create_email_verification_token(db: Session, user: User) -> EmailVerificationToken:
    """Generates a new verification token for the user."""
    # Invalidate existing unused tokens
    existing_tokens = db.scalars(
        select(EmailVerificationToken)
        .where(EmailVerificationToken.user_id == user.id, EmailVerificationToken.is_used == False)
    ).all()
    for tok in existing_tokens:
        tok.is_used = True

    token_str = generate_secure_token(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)

    token = EmailVerificationToken(
        user_id=user.id,
        token=token_str,
        expires_at=expires_at,
        is_used=False,
    )
    db.add(token)
    return token


def verify_email_token(db: Session, token_str: str) -> Tuple[bool, str, Optional[User]]:
    """Validates an email verification token and activates the associated user account."""
    token = db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token == token_str,
            EmailVerificationToken.is_used == False,
        )
    )

    if not token:
        return False, _("Invalid or already used verification token."), None

    if token.is_expired:
        return False, _("This verification link has expired. Please request a new one."), None

    token.is_used = True
    user = token.user
    user.is_verified = True
    db.commit()
    db.refresh(user)

    return True, _("Your email has been successfully verified! You can now log in."), user


def resend_verification_email(db: Session, email: str, base_url: str) -> Tuple[bool, str]:
    """Resends a verification email if account exists and is unverified."""
    user = get_user_by_email(db, email)
    if not user:
        # Don't reveal user enumeration
        return True, _("If an account exists with this email, a verification link has been sent.")

    if user.is_verified:
        return False, _("This account is already verified. You can log in.")

    token = create_email_verification_token(db, user)
    db.commit()

    verify_url = f"{base_url.rstrip('/')}/auth/verify-email?token={token.token}"
    send_verification_email(user.email, user.first_name, verify_url)

    return True, _("A new verification link has been sent to your email.")


def authenticate_user(db: Session, email: str, password: str) -> Tuple[Optional[User], str]:
    """Authenticates a user with email and password, checking active and verified statuses.

    Returns:
        Tuple of (User or None, error_message).
    """
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None, _("Invalid email or password.")

    if not user.is_active:
        return None, _("Your account has been deactivated. Please contact the administrator.")

    if not user.is_verified:
        return None, _("Your email is not verified. Please check your inbox or request a new link.")

    return user, ""


def create_password_reset_request(db: Session, email: str, base_url: str) -> Tuple[bool, str]:
    """Creates a password reset token and sends email link."""
    user = get_user_by_email(db, email)
    if not user:
        return True, _("If an account exists with this email, password reset instructions have been sent.")

    # Invalidate previous unused tokens
    existing_tokens = db.scalars(
        select(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id, PasswordResetToken.is_used == False)
    ).all()
    for tok in existing_tokens:
        tok.is_used = True

    token_str = generate_secure_token(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)

    token = PasswordResetToken(
        user_id=user.id,
        token=token_str,
        expires_at=expires_at,
        is_used=False,
    )
    db.add(token)
    db.commit()

    reset_url = f"{base_url.rstrip('/')}/auth/reset-password?token={token.token}"
    send_password_reset_email(user.email, user.first_name, reset_url)

    return True, _("If an account exists with this email, password reset instructions have been sent.")


def verify_password_reset_token(db: Session, token_str: str) -> Optional[PasswordResetToken]:
    """Validates if a password reset token is active and unexpired."""
    token = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token == token_str,
            PasswordResetToken.is_used == False,
        )
    )
    if not token or token.is_expired:
        return None
    return token


def complete_password_reset(db: Session, token_str: str, new_password: str) -> Tuple[bool, str]:
    """Updates user password and consumes the reset token."""
    token = verify_password_reset_token(db, token_str)
    if not token:
        return False, _("This password reset link is invalid or has expired.")

    user = token.user
    user.hashed_password = hash_password(new_password)
    token.is_used = True

    db.commit()
    return True, _("Your password has been reset successfully. You can now log in.")


def change_user_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> Tuple[bool, str]:
    """Changes password for a currently logged-in user verifying current password."""
    if not verify_password(current_password, user.hashed_password):
        return False, _("Incorrect current password.")

    if len(new_password) < 8:
        return False, _("New password must be at least 8 characters long.")

    user.hashed_password = hash_password(new_password)
    db.commit()
    return True, _("Your password has been changed successfully.")
