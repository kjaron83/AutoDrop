"""User and profile management business logic."""

from typing import List, Optional
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from autodrop.core.security import hash_password
from autodrop.models.user import User


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Retrieves a user by their primary key ID."""
    return db.scalar(select(User).where(User.id == user_id))


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieves a user by their email address (case-insensitive)."""
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def list_users(
    db: Session,
    search: Optional[str] = None,
    is_admin: Optional[bool] = None,
    status: Optional[str] = None,
) -> List[User]:
    """Lists users with optional search term, admin filter, and status filter.

    Args:
        db: Database session.
        search: Optional search term matching email, first_name, or last_name.
        is_admin: Optional boolean filter for admin status.
        status: Optional status filter ('active', 'inactive', 'unverified').

    Returns:
        List of matching User instances.
    """
    stmt = select(User).order_by(User.last_name, User.first_name)

    if search:
        search_pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                User.email.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
            )
        )

    if is_admin is not None:
        stmt = stmt.where(User.is_admin == is_admin)

    if status == "active":
        stmt = stmt.where(User.is_active == True, User.is_verified == True)
    elif status == "inactive":
        stmt = stmt.where(User.is_active == False)
    elif status == "unverified":
        stmt = stmt.where(User.is_verified == False)

    return list(db.scalars(stmt).all())


def update_user_profile(
    db: Session,
    user: User,
    first_name: str,
    last_name: str,
    phone: Optional[str] = None,
) -> User:
    """Updates user self-service profile information."""
    user.first_name = first_name.strip()
    user.last_name = last_name.strip()
    user.phone = phone.strip() if phone else None

    db.commit()
    db.refresh(user)
    return user


def admin_update_user(
    db: Session,
    user: User,
    first_name: str,
    last_name: str,
    phone: Optional[str],
    is_active: bool,
    is_verified: bool,
    is_admin: bool,
) -> User:
    """Admin updates user details and flags."""
    user.first_name = first_name.strip()
    user.last_name = last_name.strip()
    user.phone = phone.strip() if phone else None
    user.is_active = is_active
    user.is_verified = is_verified
    user.is_admin = is_admin

    db.commit()
    db.refresh(user)
    return user


def toggle_user_active(db: Session, user: User) -> bool:
    """Toggles user active state (soft activation/deactivation)."""
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user.is_active


def create_superuser(
    db: Session,
    email: str,
    password: str,
    first_name: str = "Admin",
    last_name: str = "User",
    phone: Optional[str] = None,
) -> User:
    """Creates or elevates an administrator account."""
    clean_email = email.strip().lower()
    user = get_user_by_email(db, clean_email)
    if user:
        user.is_admin = True
        user.is_verified = True
        user.is_active = True
        user.hashed_password = hash_password(password)
    else:
        user = User(
            email=clean_email,
            hashed_password=hash_password(password),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            phone=phone.strip() if phone else None,
            is_active=True,
            is_verified=True,
            is_admin=True,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return user
