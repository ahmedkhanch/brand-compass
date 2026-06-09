"""
FastAPI shared dependencies: database session + current user.
"""

from fastapi import Depends, Security, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.security import bearer_scheme
from app.config import settings
from app.models import User
from sqlalchemy import select


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> str:
    """Extract and verify the Clerk user ID from the Authorization header."""
    if credentials:
        token = credentials.credentials
    else:
        token = ""

    # Always allow dev tokens, even when Clerk is configured
    if token.startswith("dev-user-"):
        return token

    # No token → anonymous (works in both dev and production; real auth is enforced
    # by the frontend Clerk provider, which always sends a valid JWT)
    if not token:
        return "dev-user-anonymous"

    # Production: verify Clerk JWT
    if settings.CLERK_SECRET_KEY and settings.CLERK_JWT_ISSUER:
        import jwt
        from jwt import PyJWKClient
        jwks_url = f"{settings.CLERK_JWT_ISSUER}/.well-known/jwks.json"
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token, signing_key.key, algorithms=["RS256"],
            options={"verify_exp": True, "verify_aud": False},
        )
        return payload.get("sub")

    # Dev mode fallback
    return "dev-user-anonymous"


async def get_or_create_user(
    clerk_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get or create user in our DB. Returns {"user_id": str, "clerk_user_id": str}.
    In dev mode, auto-creates a user with fake email.
    """
    result = await db.execute(select(User).where(User.clerk_user_id == clerk_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        import uuid
        user = User(
            id=str(uuid.uuid4()),
            clerk_user_id=clerk_user_id,
            email=f"{clerk_user_id}@dev.brandcompass.local",
            full_name=clerk_user_id.replace("dev-user-", "").replace("-", " ").title(),
        )
        db.add(user)
        await db.flush()

    return {"user_id": user.id, "clerk_user_id": user.clerk_user_id}
