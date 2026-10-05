"""Admin user management routes for directory inspection and status updates."""

from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from autodrop.core.database import get_db
from autodrop.core.dependencies import require_admin
from autodrop.core.i18n import _
from autodrop.core.templates import templates
from autodrop.models.user import User
from autodrop.services.user import (
    admin_update_user,
    get_user_by_id,
    list_users,
    toggle_user_active,
)

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("", response_class=HTMLResponse)
def list_users_page(
    request: Request,
    search: Optional[str] = None,
    is_admin: Optional[str] = None,
    status: Optional[str] = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Renders the main admin user directory."""
    admin_filter: Optional[bool] = None
    if is_admin == "true":
        admin_filter = True
    elif is_admin == "false":
        admin_filter = False

    users = list_users(
        db,
        search=search,
        is_admin=admin_filter,
        status=status,
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/users/index.html",
        context={
            "users": users,
            "search": search or "",
            "selected_admin": is_admin or "",
            "selected_status": status or "",
            "current_user": admin_user,
        },
    )


@router.get("/table", response_class=HTMLResponse)
def users_table_partial(
    request: Request,
    search: Optional[str] = None,
    is_admin: Optional[str] = None,
    status: Optional[str] = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """HTMX partial endpoint to render filtered/searched user rows."""
    admin_filter: Optional[bool] = None
    if is_admin == "true":
        admin_filter = True
    elif is_admin == "false":
        admin_filter = False

    users = list_users(
        db,
        search=search,
        is_admin=admin_filter,
        status=status,
    )
    return templates.TemplateResponse(
        request=request,
        name="admin/users/partials/user_table.html",
        context={
            "users": users,
            "current_user": admin_user,
        },
    )


@router.get("/{user_id}", response_class=HTMLResponse)
def edit_user_page(
    request: Request,
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Renders the admin edit user form."""
    target_user = get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail=_("User not found."))

    return templates.TemplateResponse(
        request=request,
        name="admin/users/edit.html",
        context={
            "target_user": target_user,
            "current_user": admin_user,
        },
    )


@router.post("/{user_id}", response_class=HTMLResponse)
def handle_edit_user(
    request: Request,
    user_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: Optional[str] = Form(None),
    is_admin: bool = Form(False),
    is_active: bool = Form(False),
    is_verified: bool = Form(False),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Saves admin modifications to user profile and status flags."""
    target_user = get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail=_("User not found."))

    updated_user = admin_update_user(
        db=db,
        user=target_user,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        is_active=is_active,
        is_verified=is_verified,
        is_admin=is_admin,
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/users/edit.html",
        context={
            "target_user": updated_user,
            "current_user": admin_user,
            "message": _("User '%(name)s' updated successfully.") % {"name": updated_user.full_name},
        },
    )


@router.post("/{user_id}/toggle-status")
def handle_toggle_status(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Toggles active state of a user."""
    target_user = get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail=_("User not found."))

    toggle_user_active(db, target_user)
    return RedirectResponse(url=f"/admin/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER)
