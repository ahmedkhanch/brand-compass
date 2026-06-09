"""
Clerk JWT verification middleware.
Dev mode: when CLERK_SECRET_KEY is not set, accepts 'Bearer dev-user-{anything}'.
Production: verifies Clerk-issued JWTs via Clerk's public JWKS endpoint.
"""

from fastapi import Request, HTTPException
from app.config import settings


async def verify_clerk_token(request: Request) -> str:
    """
    Verify the Authorization header and return the user's Clerk ID.
    In dev mode (no CLERK_SECRET_KEY), accept dev tokens.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.removeprefix("Bearer ").strip()

    # ── Dev mode: accept dev-user-* tokens ──
    if not settings.CLERK_SECRET_KEY:
        if token.startswith("dev-user-"):
            return token  # clerk_user_id in dev mode
        raise HTTPException(status_code=401, detail="Dev mode: use 'Bearer dev-user-{name}'")

    # ── Production: verify Clerk JWT ──
    try:
        import jwt
        from jwt import PyJWKClient

        jwks_url = f"{settings.CLERK_JWT_ISSUER}/.well-known/jwks.json"
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=[settings.CLERK_JWT_ISSUER],
            options={"verify_exp": True},
        )
        return payload.get("sub")  # Clerk user ID
    except ImportError:
        raise HTTPException(status_code=500, detail="PyJWT not installed for Clerk production mode")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
