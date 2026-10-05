"""Email delivery service handling account verification and password reset emails."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader

from autodrop.core.config import settings

logger = logging.getLogger("autodrop.email")

# Jinja2 environment for rendering email templates
template_env = Environment(
    loader=FileSystemLoader("autodrop/templates"),
    autoescape=True,
)

# In-memory inbox for test assertions
test_outbox: List[dict] = []


def clear_test_outbox() -> None:
    """Clears the test outbox for test isolation."""
    test_outbox.clear()


def send_email(to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
    """Dispatches an email based on current environment settings.

    Args:
        to_email: Recipient email address.
        subject: Email subject line.
        html_content: HTML body.
        text_content: Optional plain text body fallback.

    Returns:
        True if sent or queued successfully, False on error.
    """
    from_name = settings.APP_NAME if settings.APP_NAME else ""
    from_header = formataddr((from_name, settings.SMTP_FROM)) if from_name else settings.SMTP_FROM
    reply_to_header = (
        formataddr((from_name, settings.APP_EMAIL))
        if (from_name and settings.APP_EMAIL)
        else settings.APP_EMAIL
    )

    if settings.is_test:
        test_outbox.append({
            "to": to_email,
            "from": from_header,
            "reply_to": reply_to_header,
            "subject": subject,
            "html": html_content,
            "text": text_content,
        })
        return True

    if settings.is_dev:
        logger.info(f"📧 [DEV EMAIL] From: {from_header} | To: {to_email} | Subject: {subject} | Reply-To: {reply_to_header}")
        # If no SMTP configured, return successfully after logging
        if not settings.SMTP_HOST:
            return True

    if not settings.SMTP_HOST:
        logger.warning("SMTP_HOST not configured, cannot send email.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_header
        msg["To"] = to_email
        if reply_to_header:
            msg["Reply-To"] = reply_to_header

        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        if settings.SMTP_TLS:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

        server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_verification_email(to_email: str, user_name: str, verification_url: str) -> bool:
    """Sends email verification link to newly registered user using templates."""
    subject = f"Verify your {settings.APP_NAME} account"
    context = {
        "app_name": settings.APP_NAME,
        "user_name": user_name,
        "verification_url": verification_url,
    }

    html_template = template_env.get_template("emails/verification.html")
    text_template = template_env.get_template("emails/verification.txt")

    html_content = html_template.render(**context)
    text_content = text_template.render(**context)

    if settings.is_dev:
        logger.info(f"🔗 [DEV VERIFICATION LINK] {verification_url}")

    return send_email(to_email, subject, html_content, text_content)


def send_password_reset_email(to_email: str, user_name: str, reset_url: str) -> bool:
    """Sends password reset link to user using templates."""
    subject = f"Reset your {settings.APP_NAME} password"
    context = {
        "app_name": settings.APP_NAME,
        "user_name": user_name,
        "reset_url": reset_url,
    }

    html_template = template_env.get_template("emails/password_reset.html")
    text_template = template_env.get_template("emails/password_reset.txt")

    html_content = html_template.render(**context)
    text_content = text_template.render(**context)

    if settings.is_dev:
        logger.info(f"🔗 [DEV RESET LINK] {reset_url}")

    return send_email(to_email, subject, html_content, text_content)
