"""
Subscription guard — require_tier() decorator for gating premium features.
Per README §8: growth features return 402 for Boussole users.
"""

from functools import wraps
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Subscription, TierEnum
from app.schemas.common import ERROR_PREMIUM_FEATURE

TIER_LEVEL = {
    TierEnum.BOUSSOLE: 0,
    TierEnum.RADAR: 1,
    TierEnum.STRATEGE: 2,
}


def require_tier(minimum: TierEnum):
    """Decorator that checks the user's subscription tier before executing the endpoint."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from kwargs — supports both bare user_id: str
            # and user: dict (the Depends(get_or_create_user) pattern)
            user = kwargs.get("user")
            if user and isinstance(user, dict):
                user_id = user.get("user_id")
            else:
                user_id = kwargs.get("user_id")
            db: AsyncSession = kwargs.get("db")

            if not user_id or not db:
                raise HTTPException(status_code=500, detail="Guard: missing user_id or db dependency")

            result = await db.execute(
                select(Subscription).where(
                    Subscription.user_id == user_id,
                    Subscription.status == "active",
                )
            )
            sub = result.scalar_one_or_none()
            user_tier = sub.tier if sub else TierEnum.BOUSSOLE

            if TIER_LEVEL.get(user_tier, 0) < TIER_LEVEL.get(minimum, 0):
                raise HTTPException(
                    status_code=402,
                    detail={
                        "code": ERROR_PREMIUM_FEATURE,
                        "message": f"This feature requires {minimum.value} tier or higher",
                    },
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
