"""Auth routes: user profile, registration. Per Sprint 2 §1."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.deps import get_or_create_user
from app.models import User, Subscription, Credit, TierEnum
from app.schemas.common import SuccessResponse, ApiResponse
from app.schemas.identity import IdentityHealthData

router = APIRouter()

TIER_LABELS = {
    TierEnum.BOUSSOLE: "Boussole",
    TierEnum.RADAR: "Radar",
    TierEnum.STRATEGE: "Stratège",
}


@router.get("/auth/me", response_model=SuccessResponse)
async def get_me(
    user: dict = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the current user's profile, subscription tier, and credit balance.
    Works in both dev mode (dev-user-* tokens) and production (Clerk JWT).
    """
    user_id = user["user_id"]

    # Get full user record
    user_result = await db.execute(select(User).where(User.id == user_id))
    user_obj = user_result.scalar_one_or_none()

    # Get subscription
    sub_result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id, Subscription.status == "active")
    )
    sub = sub_result.scalar_one_or_none()

    # Get credits
    credit_result = await db.execute(select(Credit).where(Credit.user_id == user_id))
    credit = credit_result.scalar_one_or_none()

    tier = sub.tier if sub else TierEnum.BOUSSOLE

    return SuccessResponse(
        data={
            "user_id": user_id,
            "clerk_user_id": user.get("clerk_user_id", ""),
            "email": user_obj.email if user_obj else "",
            "full_name": user_obj.full_name if user_obj else "",
            "tier": tier.value,
            "tier_label": TIER_LABELS.get(tier, "Boussole"),
            "credits_remaining": credit.balance if credit else 25,
            "subscription_status": sub.status if sub else "active",
        },
        meta={"tier": tier.value},
    )


@router.get("/health", response_model=ApiResponse[IdentityHealthData], summary="Read identity configuration status",
            description="Public readiness information. Demo identities are available only when both explicit demo switches are enabled. No secrets are returned.")
async def auth_health():
    from app.core.identity import demo_auth_enabled, identity_configured
    mode = "demo" if demo_auth_enabled() else ("clerk" if identity_configured() else "unconfigured")
    return ApiResponse(data={"status": "ok" if mode != "unconfigured" else "unconfigured",
                                 "mode": mode, "auth_provider": "Clerk" if mode == "clerk" else mode})
