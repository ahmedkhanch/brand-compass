"""Stripe service — real checkout sessions, customer portal, webhook handling."""

import stripe
from app.config import settings
from app.models import TierEnum

# Price IDs for each tier — set in .env
STRIPE_PRICES = {
    TierEnum.BOUSSOLE: settings.STRIPE_PRICE_BOUSSOLE,
    TierEnum.RADAR: settings.STRIPE_PRICE_RADAR,
    TierEnum.STRATEGE: settings.STRIPE_PRICE_STRATEGE,
}


def _stripe_ready() -> bool:
    """Check if Stripe is configured."""
    return bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_SECRET_KEY.startswith("sk_"))


async def create_checkout_session(user_id: str, user_email: str, tier: str) -> dict:
    """
    Create a Stripe Checkout session for subscription upgrade.
    Returns {checkout_url, session_id} or mock URL if Stripe isn't configured.
    """
    tier_enum = TierEnum(tier)
    price_id = STRIPE_PRICES.get(tier_enum)

    if not _stripe_ready() or not price_id or price_id == "price_xxx":
        return {
            "checkout_url": f"https://checkout.stripe.com/mock/{tier}?user={user_id}",
            "session_id": None,
            "mode": "mock",
        }

    stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.CORS_ORIGINS.split(',')[0]}/dashboard?checkout=success&tier={tier}&session={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.CORS_ORIGINS.split(',')[0]}/pricing?checkout=cancelled",
        customer_email=user_email,
        client_reference_id=user_id,
        metadata={"user_id": user_id, "tier": tier},
    )

    return {
        "checkout_url": session.url,
        "session_id": session.id,
        "mode": "live",
    }


async def create_portal_session(user_id: str, customer_id: str = None) -> dict:
    """
    Create a Stripe Customer Portal session for subscription management.
    Returns {portal_url} or mock URL if Stripe isn't configured.
    """
    if not _stripe_ready():
        return {"portal_url": f"https://billing.stripe.com/mock/portal?user={user_id}", "mode": "mock"}

    stripe.api_key = settings.STRIPE_SECRET_KEY

    if not customer_id:
        # Look up customer by user_id in Stripe
        customers = stripe.Customer.list(email=f"{user_id}@dev.brandcompass.local", limit=1)
        if customers.data:
            customer_id = customers.data[0].id

    customer_created = False
    if not customer_id:
        # Auto-create a Stripe customer for this user
        customer = stripe.Customer.create(
            email=f"{user_id}@dev.brandcompass.local",
            metadata={"user_id": user_id},
        )
        customer_id = customer.id
        customer_created = True

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{settings.CORS_ORIGINS.split(',')[0]}/dashboard",
    )

    return {
        "portal_url": session.url,
        "mode": "live",
        "customer_created": customer_created,
        "customer_id": customer_id,
    }


def verify_webhook(payload: bytes, signature: str) -> stripe.Event:
    """Verify a Stripe webhook signature. Returns the parsed event."""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe.Webhook.construct_event(
        payload, signature, settings.STRIPE_WEBHOOK_SECRET
    )
