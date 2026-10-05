"""User profile view, detail editing, and password change routes."""

from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from autodrop.core.database import get_db
from autodrop.core.dependencies import get_current_user
from autodrop.core.i18n import _
from autodrop.core.templates import templates
from autodrop.models.user import User
from autodrop.services.auth import change_user_password
from autodrop.services.user import update_user_profile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_class=HTMLResponse)
def view_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Renders user profile and password change forms."""
    return templates.TemplateResponse(
        request=request,
        name="profile/index.html",
        context={
            "user": current_user,
            "current_user": current_user,
        },
    )


@router.post("", response_class=HTMLResponse)
def handle_update_profile(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Updates user personal details."""
    updated_user = update_user_profile(
        db=db,
        user=current_user,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
    )

    return templates.TemplateResponse(
        request=request,
        name="profile/index.html",
        context={
            "user": updated_user,
            "current_user": updated_user,
            "message": _("Profile updated successfully."),
        },
    )


@router.post("/change-password", response_class=HTMLResponse)
def handle_change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Updates logged-in user password after verifying current password."""
    if new_password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="profile/index.html",
            context={
                "user": current_user,
                "current_user": current_user,
                "error": _("Passwords do not match."),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    success, msg = change_user_password(db, current_user, current_password, new_password)
    if not success:
        return templates.TemplateResponse(
            request=request,
            name="profile/index.html",
            context={
                "user": current_user,
                "current_user": current_user,
                "error": msg,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return templates.TemplateResponse(
        request=request,
        name="profile/index.html",
        context={
            "user": current_user,
            "current_user": current_user,
            "message": msg,
        },
    )
