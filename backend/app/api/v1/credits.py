"""Credit routes: balance + history."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.deps import get_or_create_user
from app.core.credit_guard import get_or_create_credits, TIER_CREDIT_MAP
from app.models import Subscription, TierEnum
from app.schemas.credit import CreditResponse
from app.schemas.common import SuccessResponse

router = APIRouter()

TIER_LABELS = {
    TierEnum.BOUSSOLE: "Boussole",
    TierEnum.RADAR: "Radar",
    TierEnum.STRATEGE: "Stratège",
}


@router.get("/credits", response_model=SuccessResponse)
async def get_credits(
    user: dict = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current credit balance + tier info."""
    user_id = user["user_id"]

    # Get tier
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id, Subscription.status == "active")
    )
    sub = result.scalar_one_or_none()
    tier = sub.tier if sub else TierEnum.BOUSSOLE

    # Get credits
    credit = await get_or_create_credits(db, user_id, tier)

    return SuccessResponse(
        data=CreditResponse(
            balance=credit.balance,
            tier=tier.value,
            tier_label=TIER_LABELS.get(tier, "Boussole"),
            max_credits=TIER_CREDIT_MAP.get(tier, 25),
            period_start=credit.period_start.isoformat() if credit.period_start else None,
            period_end=credit.period_end.isoformat() if credit.period_end else None,
        ).model_dump(),
    )
