"""
Credit guard — deducts a credit before queuing the report job.
Per README §6.3: "Credit consumed before queue."
"""

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Credit, Subscription, TierEnum
from app.config import settings
from app.schemas.common import ERROR_INSUFFICIENT_CREDITS

TIER_CREDIT_MAP = {
    TierEnum.BOUSSOLE: settings.TIER_BOUSSOLE_CREDITS,
    TierEnum.RADAR: settings.TIER_RADAR_CREDITS,
    TierEnum.STRATEGE: settings.TIER_STRATEGE_CREDITS,
}


async def get_or_create_credits(db: AsyncSession, user_id: str, tier: TierEnum) -> Credit:
    """Get user's credit row, or create one with this month's allocation."""
    result = await db.execute(select(Credit).where(Credit.user_id == user_id))
    credit = result.scalar_one_or_none()

    if credit is None:
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        # Start of current month
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # End of current month
        if now.month == 12:
            period_end = period_start.replace(year=now.year + 1, month=1)
        else:
            period_end = period_start.replace(month=now.month + 1)

        credit = Credit(
            user_id=user_id,
            balance=TIER_CREDIT_MAP.get(tier, settings.TIER_BOUSSOLE_CREDITS),
            period_start=period_start,
            period_end=period_end,
        )
        db.add(credit)
        await db.flush()

    return credit


async def deduct_credit(db: AsyncSession, user_id: str) -> Credit:
    """Deduct 1 credit. Raises 402 if balance is 0."""
    # Get user's tier
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status == "active",
        )
    )
    sub = result.scalar_one_or_none()
    tier = sub.tier if sub else TierEnum.BOUSSOLE

    credit = await get_or_create_credits(db, user_id, tier)

    if credit.balance <= 0:
        raise HTTPException(
            status_code=402,
            detail={"code": ERROR_INSUFFICIENT_CREDITS, "message": "No credits remaining this month"},
        )

    credit.balance -= 1
    await db.flush()
    return credit
