"""
POST /api/v1/brands/analyze — the core endpoint.
Validates input → deducts credit → creates brand + report rows → enqueues job.
"""

import uuid
import threading
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.deps import get_or_create_user
from app.core.credit_guard import deduct_credit
from app.core.rate_limit import check_rate_limit
from app.schemas.brand import BrandCreate
from app.schemas.report import JobResponse
from app.schemas.common import SuccessResponse
from app.models import Brand, Report, ReportStatus, Subscription, TierEnum
from app.config import settings

router = APIRouter()


async def _run_report_pipeline(user_id: str, report_id: str, brand_name: str,
                                website_url: str, industry: str, competitor: str):
    """Core pipeline: updates DB status and runs the full diagnostic."""
    import asyncio
    from app.models import Report, ReportStatus
    from app.database import async_session_factory

    # Brief pause — lets the main request's DB transaction commit
    await asyncio.sleep(1)

    async with async_session_factory() as db:
        try:
            # Update status to running
            result = await db.execute(select(Report).where(Report.id == report_id))
            report = result.scalar_one_or_none()
            if report:
                report.status = ReportStatus.RUNNING
                await db.commit()

            # Run the full pipeline from Sprint 1 (sync code → run in thread)
            from engine.orchestrator import run_full_diagnostic
            diagnostic = await asyncio.to_thread(
                run_full_diagnostic,
                brand_name=brand_name,
                website_url=website_url or "",
                industry=industry or "",
                competitor=competitor or "",
            )

            # Save results
            result = await db.execute(select(Report).where(Report.id == report_id))
            report = result.scalar_one_or_none()
            if report:
                # Strip _costs from payload before storing
                cost_records = diagnostic.pop("_costs", [])
                report.status = ReportStatus.COMPLETE
                report.payload = diagnostic
                report.scores = {
                    "seo": diagnostic.get("seo", {}).get("score") if diagnostic.get("seo") else None,
                    "geo": diagnostic.get("geo", {}).get("score") if diagnostic.get("geo") else None,
                    "overall": diagnostic.get("overall_score"),
                }
                report.generated_at = datetime.now(timezone.utc)

                # Insert cost tracking rows
                if cost_records:
                    from app.models.report_cost import ReportCost
                    for cr in cost_records:
                        db.add(ReportCost(
                            report_id=report_id,
                            provider=cr["provider"],
                            tokens_in=cr.get("tokens_in"),
                            tokens_out=cr.get("tokens_out"),
                            cost_cents=cr.get("cost_cents"),
                            duration_ms=cr.get("duration_ms"),
                        ))
                await db.commit()
        except Exception as e:
            result = await db.execute(select(Report).where(Report.id == report_id))
            report = result.scalar_one_or_none()
            if report:
                report.status = ReportStatus.FAILED
                report.error_message = str(e)
                await db.commit()


def _run_pipeline_in_thread(user_id: str, report_id: str, brand_name: str,
                            website_url: str, industry: str, competitor: str):
    """Dedicated OS thread with its own event loop.
    Completely independent of Starlette/FastAPI lifecycle — cannot be
    cancelled or dropped regardless of how the server handles requests."""
    import asyncio as _asyncio
    loop = _asyncio.new_event_loop()
    _asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            _run_report_pipeline(
                user_id, report_id, brand_name,
                website_url, industry, competitor,
            )
        )
    finally:
        loop.close()


@router.post("/brands/analyze", response_model=SuccessResponse)
async def analyze_brand(
    input: BrandCreate,
    user: dict = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a brand for analysis.
    1. Validate credit balance
    2. Deduct 1 credit
    3. Create brand + report rows
    4. Enqueue background pipeline
    5. Return job_id immediately
    """
    user_id = user["user_id"]

    # Get tier for rate limiting
    sub_result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id, Subscription.status == "active")
    )
    sub = sub_result.scalar_one_or_none()
    tier = sub.tier if sub else TierEnum.BOUSSOLE

    # Rate limit check
    await check_rate_limit(None, user_id, tier)

    # Deduct credit (raises 402 if empty)
    await deduct_credit(db, user_id)

    # Create brand row
    brand = Brand(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=input.name,
        website_url=input.website_url,
        social_accounts=input.social_accounts,
    )
    db.add(brand)

    # Create report row
    report = Report(
        id=str(uuid.uuid4()),
        user_id=user_id,
        brand_id=brand.id,
        status=ReportStatus.QUEUED,
    )
    db.add(report)
    await db.flush()

    # Enqueue the pipeline: use ARQ/Redis in production, threading in dev.
    # ARQ workers run in a separate process and scale horizontally.
    # Threading with dedicated event loop is the zero-dependency fallback.
    report_id = report.id

    if settings.REDIS_URL:
        # ── Production: Redis-backed ARQ task queue ──
        from app.jobs.report_worker import generate_report_sync
        try:
            from arq import create_pool
            from arq.connections import RedisSettings
            redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
            pool = await create_pool(redis_settings)
            await pool.enqueue_job(
                "generate_report",
                brand_input={
                    "name": input.name,
                    "website_url": input.website_url or "",
                    "industry": input.industry or "",
                    "competitor": input.competitor or "",
                },
                user_id=user_id,
                report_id=report_id,
            )
            # Don't close pool here — it's reused across requests. In production
            # you'd use a singleton pool managed at the app level.
        except Exception:
            # ARQ/Redis unavailable — fall back to threading
            thread = threading.Thread(
                target=_run_pipeline_in_thread,
                args=(user_id, report_id, input.name, input.website_url or "",
                      input.industry or "", input.competitor or ""),
                daemon=True,
            )
            thread.start()
    else:
        # ── Dev: dedicated OS thread ──
        thread = threading.Thread(
            target=_run_pipeline_in_thread,
            args=(user_id, report_id, input.name, input.website_url or "",
                  input.industry or "", input.competitor or ""),
            daemon=True,
        )
        thread.start()

    return SuccessResponse(
        data=JobResponse(
            job_id=report_id,
            report_id=report_id,
            status="queued",
        ).model_dump(),
        meta={
            "tier": tier.value,
            "credits_remaining": None,  # will be fetched by GET /credits
        },
    )
