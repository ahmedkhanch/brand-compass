"""Brand request/response schemas."""

from pydantic import BaseModel, HttpUrl
from typing import Optional


class BrandCreate(BaseModel):
    name: str
    website_url: Optional[str] = None
    social_accounts: Optional[dict] = None
    industry: Optional[str] = None
    competitor: Optional[str] = None


class BrandResponse(BaseModel):
    id: str
    user_id: str
    name: str
    website_url: Optional[str] = None
    social_accounts: Optional[dict] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}
