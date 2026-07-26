"""Auth helpers for workout sync (.env + stored token)."""

from __future__ import annotations

from pathlib import Path

import coros_api
from models import StoredAuth

_REPO_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv() -> None:
    try:
        from dotenv import load_dotenv as _load
    except ImportError:
        return
    _load(_REPO_ROOT / ".env")


def auth_status_message() -> str:
    load_dotenv()
    if coros_api.get_env_credentials():
        return "Credentials found in .env"
    auth = coros_api.get_stored_auth()
    if auth:
        return f"Using stored token (region: {auth.region})"
    return "Not configured — add COROS_EMAIL and COROS_PASSWORD to .env"


async def ensure_auth() -> StoredAuth:
    """Fresh stored token, else login via COROS_EMAIL / COROS_PASSWORD in .env."""
    load_dotenv()
    auth = coros_api.get_stored_auth()
    if auth:
        return auth
    # Prefer a real login over a TTL-expired token — expired tokens are often
    # already rejected server-side ("Access token is invalid").
    auth = await coros_api.try_auto_login()
    if auth:
        return auth
    if coros_api.get_env_credentials():
        raise RuntimeError(
            "Stored Coros token expired and COROS_EMAIL/PASSWORD in .env failed to log in. "
            "Update the password in .env, or run: coros-mcp auth"
        )
    stale = coros_api._load_auth()
    if stale:
        return stale
    raise RuntimeError(
        "Not authenticated. Copy .env.example to .env and set COROS_EMAIL, COROS_PASSWORD, "
        "and COROS_REGION (eu). Or run: coros-mcp auth-web"
    )
