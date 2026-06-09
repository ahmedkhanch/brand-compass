"""Common response schemas."""

from pydantic import BaseModel
from typing import Optional, Any


class SuccessResponse(BaseModel):
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    meta: Optional[dict] = None


class ErrorDetail(BaseModel):
    code: str
    message: str


# Standard error codes per README §8
ERROR_INSUFFICIENT_CREDITS = "INSUFFICIENT_CREDITS"
ERROR_PREMIUM_FEATURE = "PREMIUM_FEATURE"
ERROR_RATE_LIMITED = "RATE_LIMITED"
ERROR_ANALYSIS_FAILED = "ANALYSIS_FAILED"
ERROR_PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
