"""Typed report routes delegating ownership and entitlement checks to services."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_or_create_user
from app.schemas.common import ApiResponse, ApiError, AUTH_RESPONSES
from app.schemas.report import ReportResponse, ReportListResponse, DeleteReportResult, ReportAdsResult
from app.services import report_access, report_ads
from app.api.v1.report_stream import sse_router  # Compatibility with the app router.

router = APIRouter()
OWNED_RESPONSES = {**AUTH_RESPONSES, 404: {"model": ApiError, "description": "Report absent or owned by another user."}}


@router.get("/reports", response_model=ApiResponse[ReportListResponse], responses=AUTH_RESPONSES,
            summary="List your reports", description="Paginated history restricted to the authenticated owner. Reading consumes no credit.")
async def list_reports(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                       user: dict = Depends(get_or_create_user), db: AsyncSession = Depends(get_db)):
    return ApiResponse(data=await report_access.list_owned(db, user["user_id"], page, page_size))


@router.get("/reports/{report_id}", response_model=ApiResponse[ReportResponse], responses=OWNED_RESPONSES,
            summary="Read an owned report", description="Returns only fields authorized by the current subscription. Unknown and foreign IDs both return 404. No credit consumed.")
async def get_report(report_id: str, user: dict = Depends(get_or_create_user), db: AsyncSession = Depends(get_db)):
    return ApiResponse(data=await report_access.read_owned(db, report_id, user["user_id"]))


@router.delete("/reports/{report_id}", response_model=ApiResponse[DeleteReportResult], responses=OWNED_RESPONSES,
               summary="Delete an owned report", description="Deletes only a report belonging to the authenticated user. Unknown and foreign IDs both return 404.")
async def delete_report(report_id: str, user: dict = Depends(get_or_create_user), db: AsyncSession = Depends(get_db)):
    return ApiResponse(data=await report_access.delete_owned(db, report_id, user["user_id"]))


@router.get("/reports/{report_id}/meta-ads", response_model=ApiResponse[ReportAdsResult],
            responses={**OWNED_RESPONSES, 402: {"model": ApiError, "description": "Radar subscription required."}},
            summary="Read authorized report ads", description="Ownership is checked before Radar entitlement. Missing collection is explicitly unavailable, not proof of zero ads.")
async def get_meta_ads(report_id: str, user: dict = Depends(get_or_create_user), db: AsyncSession = Depends(get_db)):
    return ApiResponse(data=await report_ads.read_ads(db, report_id, user["user_id"]))
