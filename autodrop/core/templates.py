"""Shared Jinja2 template environment with internationalization (i18n) support."""

from fastapi.templating import Jinja2Templates

from autodrop.core.i18n import setup_i18n

templates = Jinja2Templates(directory="autodrop/templates")
setup_i18n(templates)
