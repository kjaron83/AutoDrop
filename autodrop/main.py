"""Main FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from autodrop.core.config import settings
from autodrop.core.dependencies import get_current_user_optional
from autodrop.core.i18n import I18nMiddleware
from autodrop.core.logging import UnhandledExceptionLoggingMiddleware, setup_logging
from autodrop.core.templates import templates
from autodrop.models.user import User
from autodrop.routes.admin_users import router as admin_users_router
from autodrop.routes.auth import router as auth_router
from autodrop.routes.profile import router as profile_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown tasks."""
    yield


# Setup application logging
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

# Add middlewares
app.add_middleware(I18nMiddleware)
app.add_middleware(UnhandledExceptionLoggingMiddleware)

# Static files mounting if directory exists
static_dir = Path("autodrop/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Register routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(admin_users_router)


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Renders the landing homepage."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "current_user": current_user,
        },
    )
