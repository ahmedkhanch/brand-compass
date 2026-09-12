"""Compatibility decorator delegating all entitlement policy to the service."""
from functools import wraps
from fastapi import HTTPException
from app.models import TierEnum
from app.services.entitlements import require_access


def require_tier(minimum: TierEnum):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("user") or {}
            user_id = user.get("user_id") or kwargs.get("user_id")
            db = kwargs.get("db")
            if not user_id or db is None:
                raise HTTPException(500, "Missing entitlement dependency")
            await require_access(db, user_id, minimum)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
