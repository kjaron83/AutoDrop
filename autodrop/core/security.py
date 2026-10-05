"""Security utilities for password hashing, token generation, and session signing."""

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict, Optional

from autodrop.core.config import settings


def hash_password(password: str) -> str:
    """Hashes a password using scrypt with a cryptographically secure random salt.

    Args:
        password: Plain text password string.

    Returns:
        Formatted string containing the algorithm parameters, salt, and hash.
    """
    salt = secrets.token_bytes(16)
    n, r, p = 16384, 8, 1
    key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        maxmem=0,
        dklen=64,
    )
    return f"scrypt${n}${r}${p}${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored hashed password string.

    Args:
        plain_password: Plain text password string.
        hashed_password: Stored hash string in format scrypt$N$r$p$salt$key.

    Returns:
        True if password matches, False otherwise.
    """
    try:
        parts = hashed_password.split("$")
        if len(parts) != 6 or parts[0] != "scrypt":
            return False

        n = int(parts[1])
        r = int(parts[2])
        p = int(parts[3])
        salt = bytes.fromhex(parts[4])
        expected_key = bytes.fromhex(parts[5])

        computed_key = hashlib.scrypt(
            plain_password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            maxmem=0,
            dklen=len(expected_key),
        )
        return hmac.compare_digest(computed_key, expected_key)
    except Exception:
        return False


def generate_secure_token(nbytes: int = 32) -> str:
    """Generates a cryptographically secure URL-safe random token string."""
    return secrets.token_urlsafe(nbytes)


def create_session_token(payload: Dict[str, Any]) -> str:
    """Creates a signed, base64-encoded session string containing timestamp and payload.

    Args:
        payload: Dictionary containing session data (e.g., {"user_id": 1}).

    Returns:
        Signed session string formatted as payload_b64.signature_hex.
    """
    data = {
        "data": payload,
        "ts": int(time.time()),
    }
    raw_json = json.dumps(data, separators=(",", ":")).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(raw_json).decode("utf-8")

    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        b64_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{b64_payload}.{signature}"


def verify_session_token(token: str, max_age_seconds: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Verifies a signed session token and checks for expiration.

    Args:
        token: Signed token string.
        max_age_seconds: Maximum allowed age in seconds (defaults to settings.SESSION_MAX_AGE_SECONDS).

    Returns:
        Payload dictionary if valid and unexpired, None otherwise.
    """
    if not token or "." not in token:
        return None

    try:
        b64_payload, signature = token.split(".", 1)

        expected_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            b64_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return None

        raw_json = base64.urlsafe_b64decode(b64_payload.encode("utf-8"))
        data = json.loads(raw_json)

        if not isinstance(data, dict) or "data" not in data or "ts" not in data:
            return None

        created_ts = data["ts"]
        max_age = max_age_seconds if max_age_seconds is not None else settings.SESSION_MAX_AGE_SECONDS
        if time.time() - created_ts > max_age:
            return None

        return data["data"]
    except Exception:
        return None
