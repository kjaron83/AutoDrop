"""Unit and integration tests for internationalization (i18n) support."""

from fastapi.testclient import TestClient
from autodrop.core.config import settings
from autodrop.core.i18n import (
    _,
    get_current_locale,
    gettext_fn,
    set_current_locale,
)


def test_translation_functions():
    """Verifies gettext behavior under different active locales."""
    try:
        # Hungarian context (default)
        set_current_locale("hu")
        assert get_current_locale() == "hu"
        assert _("Sign In") == "Bejelentkezés"
        assert _("Register") == "Regisztráció"
        assert _("Log Out") == "Kijelentkezés"

        # English context
        set_current_locale("en")
        assert get_current_locale() == "en"
        assert _("Sign In") == "Sign In"
        assert _("Register") == "Register"
    finally:
        set_current_locale(settings.DEFAULT_LOCALE)


def test_home_page_rendered_hungarian_default(client: TestClient):
    """Verifies landing page renders with default configured Hungarian strings."""
    response = client.get("/")
    assert response.status_code == 200
    assert '<html lang="hu"' in response.text
    assert "Bejelentkezés" in response.text
    assert "Regisztráció" in response.text


def test_auth_pages_hungarian_translation(client: TestClient):
    """Verifies login and register pages render Hungarian strings correctly."""
    # Login page
    login_resp = client.get("/auth/login")
    assert login_resp.status_code == 200
    assert "Bejelentkezés az AutoDrop fiókba" in login_resp.text
    assert "E-mail cím" in login_resp.text
    assert "Jelszó" in login_resp.text
    assert "Elfelejtette jelszavát?" in login_resp.text

    # Register page
    register_resp = client.get("/auth/register")
    assert register_resp.status_code == 200
    assert "Fiók létrehozása" in register_resp.text
    assert "Keresztnév" in register_resp.text
    assert "Vezetéknév" in register_resp.text
    assert "Fiók regisztrálása" in register_resp.text
