"""Server-side feature entitlements for the historical subscription tiers."""
from fastapi import HTTPException
from app.models import TierEnum
from app.repositories import subscriptions
from app.schemas.common import ERROR_PREMIUM_FEATURE

TIER_LEVEL = {TierEnum.BOUSSOLE: 0, TierEnum.RADAR: 1, TierEnum.STRATEGE: 2}
TIER_LABELS = {TierEnum.BOUSSOLE: "Boussole", TierEnum.RADAR: "Radar", TierEnum.STRATEGE: "Stratège"}


async def current_tier(db, user_id: str) -> TierEnum:
    subscription = await subscriptions.active_for_user(db, user_id)
    return subscription.tier if subscription else TierEnum.BOUSSOLE


async def has_tier(db, user_id: str, minimum: TierEnum) -> bool:
    tier = await current_tier(db, user_id)
    return TIER_LEVEL.get(tier, 0) >= TIER_LEVEL[minimum]


async def require_access(db, user_id: str, minimum: TierEnum):
    if not await has_tier(db, user_id, minimum):
        raise HTTPException(402, {"code": ERROR_PREMIUM_FEATURE,
                                 "message": f"This feature requires {minimum.value} tier or higher"})
