"""Application service for creating an authorized queued report run."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import report_job_token
from app.core.credit_guard import deduct_credit
from app.core.rate_limit import check_rate_limit
from app.repositories import report_runs
from app.schemas.brand import BrandCreate
from app.services.entitlements import current_tier


@dataclass(frozen=True)
class QueuedReport:
    report_id: str
    job_token: str
    tier: str


async def submit(db: AsyncSession, user_id: str, data: BrandCreate) -> QueuedReport:
    """Reserve a credit and persist the single brand/report pair for a request."""
    # Validate the worker boundary before rate limiting or taking a credit.
    report_job_token.require_runtime_configuration()
    tier = await current_tier(db, user_id)
    await check_rate_limit(None, user_id, tier)
    await deduct_credit(db, user_id)
    report = await report_runs.create_submission(db, user_id, data)
    # The queue may run in another process, so make the owned queued report
    # visible before handing its ID to the adapter.
    await db.commit()
    return QueuedReport(
        report_id=report.id,
        job_token=report_job_token.issue_report_job_token(
            brand_input={
                "name": data.name,
                "website_url": data.website_url or "",
                "industry": data.industry or "",
                "competitor": data.competitor or "",
            },
            user_id=user_id,
            report_id=report.id,
        ),
        tier=tier.value,
    )
