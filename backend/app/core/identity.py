"""Identity adapter: explicit local demo identities or verified Clerk JWTs."""
import asyncio
import re
from functools import lru_cache
from urllib.parse import urlsplit

import jwt
from fastapi import HTTPException
from app.config import settings


def unauthorized() -> HTTPException:
    return HTTPException(401, "Missing or invalid bearer token", headers={"WWW-Authenticate": "Bearer"})


def demo_auth_enabled() -> bool:
    return settings.DEMO_MODE and settings.ALLOW_DEMO_AUTH


def authorized_parties() -> list[str]:
    return [x.strip() for x in settings.CLERK_AUTHORIZED_PARTIES.split(",") if x.strip()]


def identity_configured() -> bool:
    issuer = settings.CLERK_JWT_ISSUER
    return bool(issuer and urlsplit(issuer).scheme == "https" and urlsplit(issuer).netloc
                and authorized_parties())


@lru_cache(maxsize=4)
def jwks_client(issuer: str):
    return jwt.PyJWKClient(f"{issuer.rstrip('/')}/.well-known/jwks.json", timeout=5)


def verified_subject(token: str) -> str:
    try:
        jwt.get_unverified_header(token)
    except jwt.InvalidTokenError:
        raise unauthorized() from None
    issuer = settings.CLERK_JWT_ISSUER
    if not identity_configured():
        raise HTTPException(503, "Identity provider is not configured")
    try:
        key = jwks_client(issuer).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token, key.key, algorithms=["RS256"], issuer=issuer,
            audience=settings.CLERK_JWT_AUDIENCE,
            options={"require": ["exp", "iat", "iss", "sub"],
                     "verify_aud": bool(settings.CLERK_JWT_AUDIENCE)},
        )
        subject = claims["sub"]
        allowed_parties = authorized_parties()
        if not isinstance(subject, str) or not subject.strip() or len(subject) > 255:
            raise unauthorized()
        if claims.get("azp") not in allowed_parties:
            raise unauthorized()
        return subject
    except jwt.PyJWKClientConnectionError:
        raise HTTPException(503, "Identity provider is temporarily unavailable") from None
    except (jwt.PyJWTError, ValueError, TypeError):
        raise unauthorized() from None


async def authenticate(token: str) -> str:
    if not token:
        raise unauthorized()
    if token.startswith("dev-user-"):
        if demo_auth_enabled() and re.fullmatch(r"dev-user-[A-Za-z0-9][A-Za-z0-9_-]{0,127}", token):
            return token
        raise unauthorized()
    return await asyncio.to_thread(verified_subject, token)
