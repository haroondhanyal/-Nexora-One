import os
from uuid import UUID
from functools import lru_cache
from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, decode
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from .db import get_db
from .api_credentials import TOKEN_PREFIX, is_expired, token_digest
from .models import ApiClientCredential, Membership

ISSUER = os.getenv("OIDC_ISSUER", "")
AUDIENCE = os.getenv("OIDC_AUDIENCE", "")
JWKS_URL = os.getenv("OIDC_JWKS_URL", "")
bearer = HTTPBearer(auto_error=False)

@lru_cache(maxsize=1)
def jwks_client(): return PyJWKClient(JWKS_URL, cache_jwk_set=True, lifespan=300)

def identity(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> dict:
    if credentials is None:
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate":"Bearer"})
    token = credentials.credentials
    if os.getenv("LOCAL_DEMO_MODE", "false").lower() == "true" and token == "local-development":
        return {"sub": "local-demo-owner", "email": "owner@nexora.local", "name": "Local Demo Owner", "email_verified": True}
    if token.startswith(TOKEN_PREFIX):
        if request.url.path in {"/api/v1/me/workspaces", "/api/v1/workspaces", "/api/v1/invitations/accept"} or request.url.path.endswith("/me/link"):
            raise HTTPException(403, "This endpoint requires an interactive workspace session")
        try:
            tenant_id = UUID(request.headers.get("x-tenant-id", ""))
        except ValueError:
            raise HTTPException(400, "A valid X-Tenant-ID is required for API credentials") from None
        db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id": str(tenant_id)})
        digest = token_digest(token)
        key = db.scalar(select(ApiClientCredential).where(ApiClientCredential.token_hash == digest, ApiClientCredential.tenant_id == tenant_id))
        if key is None or key.revoked_at is not None or is_expired(key.expires_at):
            raise HTTPException(401, "Invalid or expired API credential", headers={"WWW-Authenticate":"Bearer"})
        return {"sub": key.subject, "api_client": True, "api_tenant_id": str(key.tenant_id), "api_role": key.role, "api_branch_ids": key.branch_ids}
    try:
        signing_key = jwks_client().get_signing_key_from_jwt(token)
        return decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except Exception:
        raise HTTPException(401, "Invalid or expired session", headers={"WWW-Authenticate":"Bearer"}) from None

def membership(x_tenant_id: str | None = Header(default=None), user: dict = Depends(identity), db: Session = Depends(get_db)) -> Membership:
    if not x_tenant_id:
        raise HTTPException(400, "X-Tenant-ID header is required")
    try:
        tenant_id = UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(400, "X-Tenant-ID must be a UUID") from None
    if user.get("api_client") and str(tenant_id) != user.get("api_tenant_id"):
        raise HTTPException(403, "API credential is scoped to a different workspace")
    member = db.scalar(select(Membership).where(Membership.tenant_id == tenant_id, Membership.subject == user["sub"], Membership.active.is_(True)))
    if member is None:
        raise HTTPException(403, "Active tenant membership required")
    if user.get("api_client"):
        member = Membership(id=member.id, tenant_id=member.tenant_id, subject=member.subject, email=member.email,
                            display_name=member.display_name, role=user["api_role"], branch_ids=user["api_branch_ids"],
                            active=member.active, created_at=member.created_at)
    db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id": str(tenant_id)})
    return member

def allow(*roles: str):
    def check(member: Membership = Depends(membership)):
        if member.role not in roles:
            raise HTTPException(403, "Insufficient permission")
        return member
    return check
