"""
ARQ-compatible report generation worker.
Per README §6.3: picked up by ARQ when Redis is available.
Also callable directly as a FastAPI BackgroundTask when Redis is unavailable.
"""

import asyncio
import uuid
from datetime import datetime, timezone


async def generate_report(ctx, brand_input: dict, user_id: str, report_id: str):
    """
    ARQ worker function. Runs the full diagnostic pipeline and saves results.

    Args:
        ctx: ARQ worker context (provides Redis, etc.)
        brand_input: {name, website_url, industry, competitor, social_accounts}
        user_id: Clerk user ID
        report_id: UUID of the report row to update
    """
    from app.models import Report, ReportStatus
    from app.database import async_session_factory
    from sqlalchemy import select
    from engine.orchestrator import run_full_diagnostic

    brand_name = brand_input.get("name", "")
    website_url = brand_input.get("website_url", "")
    industry = brand_input.get("industry", "")
    competitor = brand_input.get("competitor", "")

    async with async_session_factory() as db:
        try:
            # Update to running
            result = await db.execute(select(Report).where(Report.id == report_id))
            report = result.scalar_one_or_none()
            if report:
                report.status = ReportStatus.RUNNING
                await db.commit()

            # Run pipeline in thread executor (sync code uses blocking requests)
            diagnostic = await asyncio.to_thread(
                run_full_diagnostic,
                brand_name=brand_name,
                website_url=website_url,
                industry=industry,
                competitor=competitor,
            )

            # Save
            result = await db.execute(select(Report).where(Report.id == report_id))
            report = result.scalar_one_or_none()
            if report:
                report.status = ReportStatus.COMPLETE
                report.payload = diagnostic
                report.scores = {
                    "seo": diagnostic.get("seo", {}).get("score") if diagnostic.get("seo") else None,
                    "geo": diagnostic.get("geo", {}).get("score") if diagnostic.get("geo") else None,
                    "overall": diagnostic.get("overall_score"),
                }
                report.generated_at = datetime.now(timezone.utc)
                await db.commit()

        except Exception as e:
            result = await db.execute(select(Report).where(Report.id == report_id))
            report = result.scalar_one_or_none()
            if report:
                report.status = ReportStatus.FAILED
                report.error_message = str(e)
                await db.commit()


async def generate_report_sync(brand_input: dict, user_id: str, report_id: str):
    """Synchronous wrapper for use as FastAPI BackgroundTask (no Redis)."""
    return await generate_report(None, brand_input, user_id, report_id)
