"""Credit response schemas."""

from pydantic import BaseModel
from typing import Optional


class CreditResponse(BaseModel):
    balance: int
    tier: str
    tier_label: str
    max_credits: int
    period_start: Optional[str] = None
    period_end: Optional[str] = None
