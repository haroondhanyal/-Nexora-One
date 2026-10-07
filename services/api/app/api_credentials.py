"""Pure helpers for one-time API credentials."""
import hashlib
import secrets
from datetime import datetime, timezone

TOKEN_PREFIX = "nxo_live_"
API_CLIENT_ROLES = frozenset({"Sales", "Purchasing", "Warehouse", "Finance manager"})


def new_api_token() -> str:
    return TOKEN_PREFIX + secrets.token_urlsafe(36)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def is_expired(expires_at: datetime, now: datetime | None = None) -> bool:
    current = now or datetime.now(timezone.utc)
    return expires_at <= current
