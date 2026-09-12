"""Typed account subscription responses."""
from datetime import datetime
from pydantic import BaseModel
from app.models import TierEnum


class SubscriptionData(BaseModel):
    tier: TierEnum
    tier_label: str
    status: str
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None


class CheckoutData(BaseModel):
    checkout_url: str
    tier: TierEnum
    session_id: str | None = None


class PortalData(BaseModel):
    portal_url: str
