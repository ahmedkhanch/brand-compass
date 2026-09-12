"""Account routes: a browser can request checkout, never grant itself an entitlement."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_or_create_user
from app.models import TierEnum
from app.schemas.common import ApiResponse, ApiError, AUTH_RESPONSES
from app.schemas.subscription import SubscriptionData, CheckoutData, PortalData
from app.services import account_subscription

router = APIRouter()


@router.get("/subscription", response_model=ApiResponse[SubscriptionData], responses=AUTH_RESPONSES,
            summary="Read your subscription", description="Reads persisted account rights. A user without an active subscription receives the base tier, never an implicit paid tier.")
async def get_subscription(user: dict = Depends(get_or_create_user), db: AsyncSession = Depends(get_db)):
    data = await account_subscription.status(db, user["user_id"])
    return ApiResponse(data=data, meta={"tier": data.tier.value})


@router.post("/checkout", response_model=ApiResponse[CheckoutData], responses=AUTH_RESPONSES,
             summary="Request a checkout session", description="Creates a billing-provider checkout session for the requested tier. This request does not modify account rights. The response identifies historical mock billing when Stripe is unconfigured.")
async def create_checkout(tier: TierEnum = TierEnum.RADAR, user: dict = Depends(get_or_create_user),
                          db: AsyncSession = Depends(get_db)):
    data, meta = await account_subscription.checkout(db, user["user_id"], tier)
    return ApiResponse(data=data, meta=meta)


@router.post("/checkout/portal", response_model=ApiResponse[PortalData],
             responses={**AUTH_RESPONSES, 404: {"model": ApiError, "description": "Billing portal unavailable."}},
             summary="Open your billing portal", description="Requests a portal for the authenticated account's customer reference; no customer ID is accepted from the browser.")
async def create_portal(user: dict = Depends(get_or_create_user), db: AsyncSession = Depends(get_db)):
    data, meta = await account_subscription.portal(db, user["user_id"])
    return ApiResponse(data=data, meta=meta)


@router.post("/subscription/upgrade", deprecated=True, status_code=403, response_model=ApiError,
             responses={**AUTH_RESPONSES, 403: {"model": ApiError, "description": "Direct upgrades are disabled in all modes."}},
             summary="Reject direct entitlement changes", description="Retired endpoint. Always refuses authenticated calls without modifying subscriptions or credits. Paid rights must be handled by the verified billing lifecycle.")
async def upgrade_subscription_direct(user: dict = Depends(get_or_create_user)):
    raise HTTPException(403, "Direct subscription upgrades are disabled; use verified billing")
