"""FastAPI route dependencies for authentication and authorization."""

from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from autodrop.core.config import settings
from autodrop.core.database import get_db
from autodrop.core.i18n import _
from autodrop.core.security import verify_session_token
from autodrop.models.user import User
from autodrop.services.user import get_user_by_id


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Retrieves the authenticated user from the session cookie, or None if unauthenticated."""
    cookie_name = settings.SESSION_COOKIE_NAME
    token = request.cookies.get(cookie_name)
    if not token:
        return None

    payload = verify_session_token(token)
    if not payload or "user_id" not in payload:
        return None

    user_id = payload["user_id"]
    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        return None

    return user


def get_current_user(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Enforces that the user is logged in.

    For HTMX or standard browser requests, raises 401 or redirects to login.
    """
    if not current_user:
        # Check if browser HTML request vs API
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": f"/auth/login?next={request.url.path}"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("Authentication required"),
        )
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforces that the current user has administrator privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("Access forbidden: Administrator privileges required."),
        )
    return current_user
