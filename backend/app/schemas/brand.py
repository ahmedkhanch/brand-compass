"""Brand request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class BrandCreate(BaseModel):
    name: str = Field(min_length=1)
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
