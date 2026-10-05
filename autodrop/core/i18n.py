"""Internationalization (i18n) and localization support for AutoDrop.

Provides GNU gettext integration, request-level locale resolution,
Jinja2 template extensions, and thread/async-safe translation lookup.
"""

from contextvars import ContextVar
import gettext
from pathlib import Path
from typing import Callable, Dict, List, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi.templating import Jinja2Templates

from autodrop.core.config import settings

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"

# Locale display names
LOCALE_NAMES: Dict[str, str] = {
    "hu": "Magyar",
    "en": "English",
}

# Context variables for async-safe per-request translations
_current_locale_var: ContextVar[str] = ContextVar("current_locale", default=settings.DEFAULT_LOCALE)
_current_translations_var: ContextVar[Optional[gettext.NullTranslations]] = ContextVar(
    "current_translations", default=None
)

# In-memory translation catalog cache
_translations_cache: Dict[str, gettext.NullTranslations] = {}


def get_current_locale() -> str:
    """Returns the active locale code for the current execution context.

    Returns:
        str: Active ISO 639-1 language code (e.g., 'hu', 'en').
    """
    return _current_locale_var.get()


def get_translation(locale: Optional[str] = None) -> gettext.NullTranslations:
    """Loads and caches the GNU gettext translation catalog for a given locale.

    Args:
        locale: Optional language code. If None, uses the current context locale.

    Returns:
        gettext.NullTranslations: Loaded or fallback gettext translation object.
    """
    target_locale = locale or get_current_locale()
    if target_locale not in settings.SUPPORTED_LOCALES:
        target_locale = settings.DEFAULT_LOCALE

    # Always return cached instance if available
    if target_locale in _translations_cache:
        return _translations_cache[target_locale]

    try:
        trans = gettext.translation(
            domain="messages",
            localedir=str(LOCALES_DIR),
            languages=[target_locale],
            fallback=True,
        )
    except Exception:
        trans = gettext.NullTranslations()

    _translations_cache[target_locale] = trans
    return trans


def set_current_locale(locale: str) -> None:
    """Sets the active locale and translation catalog in the current context.

    Args:
        locale: The language code to activate.
    """
    if locale not in settings.SUPPORTED_LOCALES:
        locale = settings.DEFAULT_LOCALE

    _current_locale_var.set(locale)
    _current_translations_var.set(get_translation(locale))


def gettext_fn(message: str) -> str:
    """Translates a message using the active context's translation catalog.

    Args:
        message: The source string to translate.

    Returns:
        str: The translated string if available, or the original message.
    """
    trans = _current_translations_var.get()
    if trans is None:
        trans = get_translation()
    return trans.gettext(message)


def ngettext_fn(singular: str, plural: str, n: int) -> str:
    """Translates a pluralized message using the active context's catalog.

    Args:
        singular: Singular source string.
        plural: Plural source string.
        n: The count determine singular vs plural form.

    Returns:
        str: The translated singular or plural string.
    """
    trans = _current_translations_var.get()
    if trans is None:
        trans = get_translation()
    return trans.ngettext(singular, plural, n)


def gettext_noop(message: str) -> str:
    """Marks a message string for Babel translation extraction without translating it at runtime.

    Args:
        message: The source string to mark.

    Returns:
        str: The unmodified canonical string.
    """
    return message


# Aliases for gettext
_ = gettext_fn
N_ = gettext_noop


class I18nMiddleware(BaseHTTPMiddleware):
    """Middleware that binds the configured default locale and translations to contextvars."""

    def __init__(self, app: ASGIApp):
        """Initializes the i18n middleware.

        Args:
            app: The ASGI application instance.
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        """Processes the request, setting context variables for locale and gettext.

        Args:
            request: The incoming request.
            call_next: Next ASGI handler.

        Returns:
            Response: The HTTP response.
        """
        locale = settings.DEFAULT_LOCALE
        set_current_locale(locale)
        request.state.locale = locale
        response = await call_next(request)
        return response


def setup_i18n(templates: Jinja2Templates) -> None:
    """Configures the Jinja2 template environment for i18n with gettext callables.

    Args:
        templates: The FastAPI Jinja2Templates instance.
    """
    templates.env.add_extension("jinja2.ext.i18n")
    templates.env.install_gettext_callables(gettext_fn, ngettext_fn, newstyle=True)
    templates.env.globals["get_current_locale"] = get_current_locale
    templates.env.globals["DEFAULT_LOCALE"] = settings.DEFAULT_LOCALE
    templates.env.globals["LOCALE_NAMES"] = LOCALE_NAMES
    templates.env.globals["_"] = gettext_fn
