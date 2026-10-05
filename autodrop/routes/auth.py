"""Authentication routes: registration, verification, login, logout, and password resets."""

from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from autodrop.core.config import settings
from autodrop.core.database import get_db
from autodrop.core.dependencies import get_current_user_optional
from autodrop.core.i18n import _
from autodrop.core.security import create_session_token
from autodrop.core.templates import templates
from autodrop.models.user import User
from autodrop.services.auth import (
    authenticate_user,
    complete_password_reset,
    create_password_reset_request,
    register_user,
    resend_verification_email,
    verify_email_token,
    verify_password_reset_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/register", response_class=HTMLResponse)
def register_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Renders the self-registration form."""
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="auth/register.html",
        context={"current_user": None},
    )


@router.post("/register", response_class=HTMLResponse)
def handle_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Processes user registration, creating unverified account and sending confirmation email."""
    if len(password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "error": _("Password must be at least 8 characters long."),
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "current_user": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    base_url = str(request.base_url)
    user, msg = register_user(
        db=db,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        base_url=base_url,
    )

    if not user:
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "error": msg,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "current_user": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(
        url=f"/auth/verify-notice?email={user.email}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/verify-notice", response_class=HTMLResponse)
def verify_notice_page(request: Request, email: str = ""):
    """Displays check email verification notice."""
    return templates.TemplateResponse(
        request=request,
        name="auth/verify_notice.html",
        context={"email": email, "current_user": None},
    )


@router.get("/verify-email", response_class=HTMLResponse)
def verify_email_link(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
):
    """Validates verification token clicked from email link."""
    success, msg, user = verify_email_token(db, token)
    if not success:
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={"error": msg, "current_user": None},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={"message": msg, "email": user.email if user else "", "current_user": None},
    )


@router.post("/resend-verification", response_class=HTMLResponse)
def handle_resend_verification(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    """Resends email verification link."""
    base_url = str(request.base_url)
    success, msg = resend_verification_email(db, email, base_url)
    return templates.TemplateResponse(
        request=request,
        name="auth/verify_notice.html",
        context={"email": email, "message": msg if success else None, "error": msg if not success else None, "current_user": None},
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    next: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Renders login page."""
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={"next": next, "current_user": None},
    )


@router.post("/login", response_class=HTMLResponse)
def handle_login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    next: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Processes login credentials and sets secure session cookie."""
    user, error_msg = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={"error": error_msg, "email": email, "next": next, "current_user": None},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    redirect_url = next if next and next.startswith("/") else "/"
    res = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    session_token = create_session_token({"user_id": user.id})
    res.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.is_prod,
    )
    return res


@router.post("/logout")
def handle_logout(response: Response):
    """Clears user session cookie and redirects to login."""
    res = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    res.delete_cookie(key=settings.SESSION_COOKIE_NAME)
    return res


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    """Renders forgot password request form."""
    return templates.TemplateResponse(
        request=request,
        name="auth/forgot_password.html",
        context={"current_user": None},
    )


@router.post("/forgot-password", response_class=HTMLResponse)
def handle_forgot_password(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    """Processes password reset request and dispatches reset link."""
    base_url = str(request.base_url)
    success, msg = create_password_reset_request(db, email, base_url)
    return templates.TemplateResponse(
        request=request,
        name="auth/forgot_password.html",
        context={"message": msg, "current_user": None},
    )


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
):
    """Renders new password entry form if token is valid."""
    reset_tok = verify_password_reset_token(db, token)
    if not reset_tok:
        return templates.TemplateResponse(
            request=request,
            name="auth/forgot_password.html",
            context={"error": _("Password reset link is invalid or has expired."), "current_user": None},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return templates.TemplateResponse(
        request=request,
        name="auth/reset_password.html",
        context={"token": token, "current_user": None},
    )


@router.post("/reset-password", response_class=HTMLResponse)
def handle_reset_password(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Sets new password upon token submission."""
    if password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="auth/reset_password.html",
            context={"token": token, "error": _("Passwords do not match."), "current_user": None},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if len(password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="auth/reset_password.html",
            context={"token": token, "error": _("Password must be at least 8 characters long."), "current_user": None},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    success, msg = complete_password_reset(db, token, password)
    if not success:
        return templates.TemplateResponse(
            request=request,
            name="auth/forgot_password.html",
            context={"error": msg, "current_user": None},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={"message": msg, "current_user": None},
    )
