"""
POST /api/v1/brands/analyze — the core endpoint.
Validates input → delegates submission → enqueues the authorized report job.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_or_create_user
from app.schemas.brand import BrandCreate
from app.schemas.common import ApiError, AUTH_RESPONSES
from app.schemas.report import AnalyzeReportMeta, AnalyzeReportResponse, JobResponse
from app.jobs.dispatch import enqueue_report
from app.services import report_submission

router = APIRouter()

ANALYZE_RESPONSES = {
    **AUTH_RESPONSES,
    402: {"model": ApiError, "description": "No report credit remains for the current period."},
    429: {"model": ApiError, "description": "The tier-specific submission limit is exceeded."},
    503: {"model": ApiError, "description": "Identity or internal report-job execution is unavailable."},
}


@router.post(
    "/brands/analyze",
    response_model=AnalyzeReportResponse,
    summary="Submit an owned brand analysis",
    description="Reserves one credit, creates one queued report, and enqueues its authorized job.",
    responses=ANALYZE_RESPONSES,
)
async def analyze_brand(
    input: BrandCreate,
    user: dict = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit one authenticated brand analysis and enqueue its report run.

    The route does not persist models directly. The submission service reserves
    the existing one-credit policy and creates the owned queued report before
    the queue adapter receives the job.
    """
    job = await report_submission.submit(db, user["user_id"], input)
    await enqueue_report(job)

    return AnalyzeReportResponse(
        data=JobResponse(
            job_id=job.report_id,
            report_id=job.report_id,
            status="queued",
        ).model_dump(),
        meta=AnalyzeReportMeta(
            tier=job.tier,
            credits_remaining=None,  # will be fetched by GET /credits
        ),
    )
