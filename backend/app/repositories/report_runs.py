"""SQLAlchemy persistence for submitted report runs and their results."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Brand, Report, ReportCost, ReportStatus
from app.schemas.brand import BrandCreate


async def create_submission(db: AsyncSession, user_id: str, data: BrandCreate) -> Report:
    brand = Brand(
        user_id=user_id,
        name=data.name,
        website_url=data.website_url,
        social_accounts=data.social_accounts,
    )
    db.add(brand)
    await db.flush()

    report = Report(
        user_id=user_id,
        brand_id=brand.id,
        status=ReportStatus.QUEUED,
    )
    db.add(report)
    await db.flush()
    return report


async def owned(db: AsyncSession, report_id: str, user_id: str) -> Report | None:
    return (await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == user_id)
    )).scalar_one_or_none()


async def mark_running(db: AsyncSession, report_id: str, user_id: str) -> bool:
    report = await owned(db, report_id, user_id)
    if report is None:
        return False
    report.status = ReportStatus.RUNNING
    await db.flush()
    return True


async def complete(db: AsyncSession, report_id: str, user_id: str, diagnostic: dict) -> bool:
    report = await owned(db, report_id, user_id)
    if report is None:
        return False

    cost_records = diagnostic.get("_costs", [])
    report.status = ReportStatus.COMPLETE
    report.payload = {key: value for key, value in diagnostic.items() if key != "_costs"}
    report.scores = {
        "seo": diagnostic.get("seo", {}).get("score") if diagnostic.get("seo") else None,
        "geo": diagnostic.get("geo", {}).get("score") if diagnostic.get("geo") else None,
        "overall": diagnostic.get("overall_score"),
    }
    report.generated_at = datetime.now(timezone.utc)

    for cost in cost_records:
        db.add(ReportCost(
            report_id=report.id,
            provider=cost["provider"],
            tokens_in=cost.get("tokens_in"),
            tokens_out=cost.get("tokens_out"),
            cost_cents=cost.get("cost_cents"),
            duration_ms=cost.get("duration_ms"),
        ))
    await db.flush()
    return True


async def fail(db: AsyncSession, report_id: str, user_id: str, message: str) -> bool:
    report = await owned(db, report_id, user_id)
    if report is None:
        return False
    report.status = ReportStatus.FAILED
    report.error_message = message
    await db.flush()
    return True
