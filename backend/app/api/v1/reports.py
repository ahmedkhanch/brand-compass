"""
Report routes: list, get, delete, SSE streaming.
"""

import asyncio
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.core.deps import get_or_create_user
from app.models import Report, ReportStatus, Brand, Subscription, TierEnum
from app.schemas.report import ReportResponse, ReportListItem, ReportListResponse
from app.schemas.common import SuccessResponse, ERROR_PREMIUM_FEATURE
from app.core.subscription_guard import require_tier

router = APIRouter()


@router.get("/reports", response_model=SuccessResponse)
async def list_reports(
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """List the user's reports, newest first."""
    user_id = user["user_id"]
    offset = (page - 1) * page_size

    result = await db.execute(
        select(Report)
        .where(Report.user_id == user_id)
        .order_by(desc(Report.created_at))
        .offset(offset)
        .limit(page_size)
    )
    reports = result.scalars().all()

    # Count total
    count_result = await db.execute(
        select(Report).where(Report.user_id == user_id)
    )
    total = len(count_result.scalars().all())

    items = []
    for r in reports:
        # Get brand name
        brand_name = None
        if r.brand_id:
            b_result = await db.execute(select(Brand).where(Brand.id == r.brand_id))
            brand = b_result.scalar_one_or_none()
            if brand:
                brand_name = brand.name

        items.append(ReportListItem(
            id=r.id,
            brand_name=brand_name,
            status=r.status.value,
            scores=r.scores,
            created_at=r.created_at.isoformat() if r.created_at else None,
        ))

    return SuccessResponse(
        data=ReportListResponse(
            reports=items,
            total=total,
            page=page,
            page_size=page_size,
        ).model_dump(),
    )


@router.get("/reports/{report_id}", response_model=SuccessResponse)
async def get_report(
    report_id: str,
    user: dict = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single report by ID."""
    user_id = user["user_id"]

    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == user_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return SuccessResponse(
        data=ReportResponse(
            id=report.id,
            user_id=report.user_id,
            brand_id=report.brand_id,
            status=report.status.value,
            payload=report.payload,
            scores=report.scores,
            error_message=report.error_message,
            generated_at=report.generated_at.isoformat() if report.generated_at else None,
            created_at=report.created_at.isoformat() if report.created_at else None,
            expires_at=report.expires_at.isoformat() if report.expires_at else None,
        ).model_dump(),
    )


@router.delete("/reports/{report_id}", response_model=SuccessResponse)
async def delete_report(
    report_id: str,
    user: dict = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a report."""
    user_id = user["user_id"]

    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == user_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    await db.delete(report)
    await db.flush()

    return SuccessResponse(data={"deleted": True})


@router.get("/reports/{report_id}/meta-ads")
@require_tier(TierEnum.RADAR)
async def get_meta_ads(
    report_id: str,
    user: dict = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """Meta Ads section — Radar+ only. Returns Facebook/Instagram ad library data."""
    user_id = user["user_id"]
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == user_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check if meta ads data already exists in the payload
    if report.payload and report.payload.get("meta_ads"):
        return SuccessResponse(
            data={"report_id": report_id, "meta_ads": report.payload["meta_ads"]},
            meta={"tier": "radar", "source": "cached"},
        )

    # Fetch on demand via Apify
    brand_name = None
    if report.payload:
        brand_name = report.payload.get("brand")

    if not brand_name:
        # Fallback: get from brand table
        brand_result = await db.execute(select(Brand).where(Brand.id == report.brand_id))
        brand = brand_result.scalar_one_or_none()
        if brand:
            brand_name = brand.name

    if not brand_name:
        return SuccessResponse(
            data={"report_id": report_id, "meta_ads": None, "error": "No brand name found"},
            meta={"tier": "radar"},
        )

    # Scrape Meta Ads from Apify
    try:
        from engine.providers.apify import ApifyProvider, ApifyError
        from engine.providers.mock import demo_enabled, MockApify
        apify = MockApify(brand_name=brand_name) if demo_enabled() else ApifyProvider()
        ads = apify.search_meta_ads(brand_name, max_results=20)

        summary = {
            "total_ads_found": len(ads),
            "brand_name": brand_name,
            "ads": ads[:10],  # top 10 ads
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

        # Cache in report payload
        if report.payload:
            report.payload["meta_ads"] = summary
            await db.commit()

        return SuccessResponse(
            data={"report_id": report_id, "meta_ads": summary},
            meta={"tier": "radar", "source": "live"},
        )
    except ApifyError as e:
        # Apify not available (requires Growth+ tier) — return graceful message
        return SuccessResponse(
            data={"report_id": report_id, "meta_ads": None, "error": str(e)},
            meta={"tier": "radar", "source": "unavailable"},
        )
    except Exception as e:
        return SuccessResponse(
            data={"report_id": report_id, "meta_ads": None, "error": f"Apify error: {str(e)}"},
            meta={"tier": "radar", "source": "error"},
        )


# ── SSE endpoint (outside /api/v1 prefix, per README §8) ──

sse_router = APIRouter()


@sse_router.get("/sse/reports/{report_id}")
async def stream_report_progress(
    report_id: str,
    user: dict = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """
    SSE endpoint — streams report progress to the frontend.
    Frontend opens this after POST /brands/analyze to get live updates.
    """
    user_id = user["user_id"]

    async def event_stream():
        last_status = None
        for _ in range(180):  # max 180 iterations × 1s = 3 minutes
            # Expire cached objects so SELECT re-reads from the DB.
            db.expire_all()
            result = await db.execute(
                select(Report).where(Report.id == report_id)
            )
            report = result.scalar_one_or_none()
            current_status = report.status.value if report else None
            # End this read transaction so the next poll starts a fresh snapshot
            # (SQLite holds a repeatable-read snapshot until the txn closes) and
            # so the writer pipeline is never blocked by a long-lived reader.
            await db.rollback()

            if not report:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Report not found'})}\n\n"
                return

            if current_status != last_status:
                yield f"data: {json.dumps({'status': current_status, 'report_id': report_id})}\n\n"
                last_status = current_status

            if current_status in ("complete", "failed"):
                return

            await asyncio.sleep(1)

        yield f"data: {json.dumps({'status': 'timeout', 'message': 'Report took too long'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
