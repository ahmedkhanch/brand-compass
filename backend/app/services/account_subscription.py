"""Account subscription reads and billing adapter orchestration."""
from fastapi import HTTPException
from app.models import TierEnum
from app.repositories import subscriptions, users
from app.services.entitlements import TIER_LABELS
from app.schemas.subscription import SubscriptionData, CheckoutData, PortalData


async def status(db, user_id: str):
    sub = await subscriptions.active_for_user(db, user_id)
    tier = sub.tier if sub else TierEnum.BOUSSOLE
    return SubscriptionData(tier=tier, tier_label=TIER_LABELS[tier],
                            status=sub.status if sub else "inactive",
                            current_period_start=sub.current_period_start if sub else None,
                            current_period_end=sub.current_period_end if sub else None)


async def checkout(db, user_id: str, tier: TierEnum):
    from app.services.stripe import create_checkout_session
    user = await users.by_id(db, user_id)
    result = await create_checkout_session(user_id=user_id, user_email=user.email, tier=tier.value)
    return CheckoutData(checkout_url=result["checkout_url"], tier=tier,
                        session_id=result.get("session_id")), {"mode": result.get("mode")}


async def portal(db, user_id: str):
    from app.services.stripe import create_portal_session
    sub = await subscriptions.active_for_user(db, user_id)
    result = await create_portal_session(user_id=user_id, customer_id=sub.stripe_cust_id if sub else None)
    if result.get("error"):
        raise HTTPException(404, "Billing portal unavailable")
    if result.get("customer_created") and sub:
        await subscriptions.set_customer(db, sub, result.get("customer_id"))
    return PortalData(portal_url=result["portal_url"]), {"mode": result.get("mode")}
