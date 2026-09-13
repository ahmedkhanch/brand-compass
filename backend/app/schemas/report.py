"""Report request/response schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobResponse(BaseModel):
    job_id: str
    report_id: str
    status: str = "queued"


class AnalyzeReportMeta(BaseModel):
    tier: str
    credits_remaining: int | None = None


class AnalyzeReportResponse(BaseModel):
    success: bool = True
    data: JobResponse
    error: None = None
    meta: AnalyzeReportMeta


class ReportResponse(BaseModel):
    id: str
    user_id: str
    brand_id: str
    status: str
    payload: Optional[dict] = None
    scores: Optional[dict] = None
    error_message: Optional[str] = None
    generated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReportListItem(BaseModel):
    id: str
    brand_name: Optional[str] = None
    status: str
    scores: Optional[dict] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    reports: list[ReportListItem]
    total: int
    page: int = 1
    page_size: int = 20


class DeleteReportResult(BaseModel):
    deleted: bool


class ReportAdsResult(BaseModel):
    report_id: str
    meta_ads: Optional[dict] = None
    availability: Optional[str] = None
