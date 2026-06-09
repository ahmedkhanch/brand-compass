"""Stripe webhook receiver — handles subscription lifecycle events."""

import logging
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select
from app.database import async_session_factory
from app.schemas.common import SuccessResponse
from app.config import settings

router = APIRouter()
logger = logging.getLogger("brand_compass.stripe")


async def _handle_checkout_completed(event_data: dict):
    """Create or upgrade a subscription after successful Stripe checkout."""
    from app.models import User, Subscription, Credit, TierEnum
    from datetime import datetime, timezone

    customer_email = event_data.get("customer_email") or event_data.get("customer_details", {}).get("email")
    metadata = event_data.get("metadata", {})
    user_id = metadata.get("user_id")
    tier = metadata.get("tier", "boussole")

    if not user_id or not customer_email:
        logger.warning("Webhook missing user_id or email in checkout metadata")
        return

    async with async_session_factory() as db:
        # Find or create user
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            import uuid
            user = User(
                id=user_id,
                clerk_user_id=user_id,
                email=customer_email,
            )
            db.add(user)
            await db.flush()

        # Upsert subscription
        sub_result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        sub = sub_result.scalar_one_or_none()

        if sub:
            sub.tier = TierEnum(tier)
            sub.status = "active"
            sub.stripe_cust_id = event_data.get("customer")
            sub.stripe_sub_id = event_data.get("subscription")
            sub.current_period_start = datetime.now(timezone.utc)
            sub.updated_at = datetime.now(timezone.utc)
        else:
            sub = Subscription(
                user_id=user_id,
                tier=TierEnum(tier),
                status="active",
                stripe_cust_id=event_data.get("customer"),
                stripe_sub_id=event_data.get("subscription"),
            )
            db.add(sub)

        # Reset credits for the new billing period
        from app.core.credit_guard import TIER_CREDIT_MAP
        credit_result = await db.execute(select(Credit).where(Credit.user_id == user_id))
        credit = credit_result.scalar_one_or_none()
        if credit:
            credit.balance = TIER_CREDIT_MAP.get(TierEnum(tier), 25)
        else:
            now = datetime.now(timezone.utc)
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            credit = Credit(
                user_id=user_id,
                balance=TIER_CREDIT_MAP.get(TierEnum(tier), 25),
                period_start=period_start,
            )
            db.add(credit)

        await db.commit()
        logger.info(f"Webhook: user {user_id[:8]} upgraded to {tier}")


async def _handle_invoice_paid(event_data: dict):
    """Reset monthly credit balance when an invoice is paid."""
    from app.models import Subscription, Credit
    from app.core.credit_guard import TIER_CREDIT_MAP

    customer_id = event_data.get("customer")
    if not customer_id:
        return

    async with async_session_factory() as db:
        sub_result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_cust_id == customer_id,
                Subscription.status == "active",
            )
        )
        sub = sub_result.scalar_one_or_none()
        if not sub:
            return

        credit_result = await db.execute(select(Credit).where(Credit.user_id == sub.user_id))
        credit = credit_result.scalar_one_or_none()
        if credit:
            credit.balance = TIER_CREDIT_MAP.get(sub.tier, 25)
            await db.commit()
            logger.info(f"Webhook: credits reset for user {sub.user_id[:8]}")


async def _handle_subscription_deleted(event_data: dict):
    """Downgrade user to Boussole when subscription is cancelled."""
    from app.models import Subscription, TierEnum
    from datetime import datetime, timezone

    customer_id = event_data.get("customer")
    if not customer_id:
        return

    async with async_session_factory() as db:
        sub_result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_cust_id == customer_id,
                Subscription.status == "active",
            )
        )
        sub = sub_result.scalar_one_or_none()
        if sub:
            sub.tier = TierEnum.BOUSSOLE
            sub.status = "active"
            sub.stripe_sub_id = None
            sub.updated_at = datetime.now(timezone.utc)
            await db.commit()
            logger.info(f"Webhook: user {sub.user_id[:8]} downgraded to boussole")


WEBHOOK_HANDLERS = {
    "checkout.session.completed": _handle_checkout_completed,
    "invoice.paid": _handle_invoice_paid,
    "customer.subscription.deleted": _handle_subscription_deleted,
}


@router.post("/webhooks/stripe", response_model=SuccessResponse)
async def stripe_webhook(request: Request):
    """
    Receive Stripe webhooks and update subscription state.
    Only Stripe calls this — not meant for manual Swagger testing.
    """
    body = await request.body()
    signature = request.headers.get("stripe-signature", "")

    # Without a signature, this is a manual test call — return helpful info
    if not signature:
        return SuccessResponse(
            data={"received": True},
            meta={
                "mode": "manual",
                "note": "This endpoint is for Stripe webhooks only. "
                        "Stripe calls it automatically after checkout.session.completed, "
                        "invoice.paid, and customer.subscription.deleted events. "
                        "Use 'stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe' to test locally."
            },
        )

    # Only verify if BOTH keys are configured (not placeholders)
    stripe_ready = (
        settings.STRIPE_SECRET_KEY
        and settings.STRIPE_SECRET_KEY.startswith("sk_")
        and settings.STRIPE_WEBHOOK_SECRET
        and settings.STRIPE_WEBHOOK_SECRET.startswith("whsec_")
    )
    if stripe_ready:
        try:
            from app.services.stripe import verify_webhook
            event = verify_webhook(body, signature)
            event_type = event.get("type", "")
            event_data = event.get("data", {}).get("object", {})

            handler = WEBHOOK_HANDLERS.get(event_type)
            if handler:
                await handler(event_data)
                return SuccessResponse(
                    data={"received": True, "event": event_type, "action": "processed"},
                    meta={"mode": "live"},
                )
            else:
                logger.info(f"Unhandled webhook event: {event_type}")
                return SuccessResponse(
                    data={"received": True, "event": event_type, "action": "skipped"},
                    meta={"mode": "live", "note": f"No handler for {event_type}"},
                )
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

    # Stripe not configured — stub mode
    return SuccessResponse(
        data={"received": True},
        meta={"mode": "stub", "note": "Stripe not configured — add STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET to .env"},
    )
