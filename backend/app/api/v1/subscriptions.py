"""Subscription routes: Stripe checkout + portal."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.deps import get_or_create_user
from app.models import Subscription, TierEnum, User, Credit
from app.schemas.common import SuccessResponse

router = APIRouter()

TIER_LABELS = {
    TierEnum.BOUSSOLE: "Boussole",
    TierEnum.RADAR: "Radar",
    TierEnum.STRATEGE: "Stratège",
}
VALID_TIERS = {"boussole", "radar", "stratege"}


@router.get("/subscription", response_model=SuccessResponse)
async def get_subscription(
    user: dict = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current subscription status + tier."""
    user_id = user["user_id"]

    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id, Subscription.status == "active")
    )
    sub = result.scalar_one_or_none()

    if sub:
        return SuccessResponse(
            data={
                "tier": sub.tier.value,
                "tier_label": TIER_LABELS.get(sub.tier, "Boussole"),
                "status": sub.status,
                "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
                "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
            },
            meta={"tier": sub.tier.value},
        )
    else:
        return SuccessResponse(
            data={"tier": "radar", "tier_label": "Radar", "status": "active"},
            meta={"tier": "radar"},
        )


@router.post("/checkout", response_model=SuccessResponse)
async def create_checkout(
    tier: str = "radar",
    user: dict = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Stripe Checkout session for upgrading to the given tier.
    Falls back to mock URL if Stripe isn't configured.
    """
    if tier not in VALID_TIERS:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}. Use one of: {', '.join(sorted(VALID_TIERS))}")

    from app.services.stripe import create_checkout_session
    from app.models import User

    # Get user email
    user_result = await db.execute(select(User).where(User.id == user["user_id"]))
    user_obj = user_result.scalar_one_or_none()
    user_email = user_obj.email if user_obj else f"{user['user_id']}@dev.brandcompass.local"

    result = await create_checkout_session(
        user_id=user["user_id"],
        user_email=user_email,
        tier=tier,
    )

    msg = "Live Stripe session" if result.get("mode") == "live" else "Mock URL — Stripe not configured"
    return SuccessResponse(
        data={"checkout_url": result["checkout_url"], "tier": tier, "session_id": result.get("session_id")},
        meta={"mode": result.get("mode"), "note": msg},
    )


@router.post("/checkout/portal", response_model=SuccessResponse)
async def create_portal(
    user: dict = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Stripe Customer Portal session for managing subscriptions.
    Falls back to mock URL if Stripe isn't configured.
    """
    from app.services.stripe import create_portal_session

    # Check for existing Stripe customer ID
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user["user_id"], Subscription.status == "active")
    )
    sub = result.scalar_one_or_none()
    stripe_cust_id = sub.stripe_cust_id if sub else None

    portal_result = await create_portal_session(
        user_id=user["user_id"],
        customer_id=stripe_cust_id,
    )

    if portal_result.get("error"):
        raise HTTPException(status_code=404, detail=portal_result["error"])

    # If a new customer was auto-created, save the customer_id to the subscription
    if portal_result.get("customer_created") and sub:
        sub.stripe_cust_id = portal_result.get("customer_id")
        await db.commit()

    msg = "Live Stripe portal" if portal_result.get("mode") == "live" else "Mock URL — Stripe not configured"
    return SuccessResponse(
        data={"portal_url": portal_result["portal_url"]},
        meta={"mode": portal_result.get("mode"), "note": msg},
    )


@router.post("/subscription/upgrade", response_model=SuccessResponse)
async def upgrade_subscription_direct(
    tier: str,
    user: dict = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Directly upgrade the user's subscription tier (for dev/testing/localhost).
    In production, upgrades happen via Stripe webhooks.
    """
    if tier not in VALID_TIERS:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")

    import uuid
    from datetime import datetime, timezone

    user_id = user["user_id"]
    tier_enum = TierEnum(tier)

    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    sub = result.scalar_one_or_none()

    if sub:
        sub.tier = tier_enum
        sub.status = "active"
        sub.updated_at = datetime.now(timezone.utc)
    else:
        sub = Subscription(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tier=tier_enum,
            status="active",
        )
        db.add(sub)

    # Reset credits for the new tier
    from app.core.credit_guard import TIER_CREDIT_MAP
    credit_result = await db.execute(select(Credit).where(Credit.user_id == user_id))
    credit = credit_result.scalar_one_or_none()
    if credit:
        credit.balance = TIER_CREDIT_MAP.get(tier_enum, 25)

    await db.commit()
    return SuccessResponse(
        data={"tier": tier, "status": "active"},
        meta={"note": "Tier upgraded directly (localhost dev mode)"},
    )
