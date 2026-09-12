"""Owned report access and response projection; never return paid data by accident."""
from fastapi import HTTPException
from app.models import TierEnum
from app.repositories import reports
from app.schemas.report import ReportResponse, ReportListItem, ReportListResponse
from app.services.entitlements import has_tier

PUBLIC_REPORT_FIELDS = frozenset({
    "brand", "website", "industry", "competitor", "website_content", "positioning", "swot",
    "competitive", "recommendations", "seo", "geo", "overall_score", "completed_at",
})
SCORE_FIELDS = frozenset({"seo", "geo", "overall"})


def visible_scores(scores):
    return {k: v for k, v in (scores or {}).items() if k in SCORE_FIELDS} or None


async def owned_report(db, report_id: str, user_id: str):
    report = await reports.owned(db, report_id, user_id)
    if report is None:
        raise HTTPException(404, "Report not found")
    return report


async def list_owned(db, user_id: str, number: int, size: int):
    rows, total = await reports.page(db, user_id, number, size)
    return ReportListResponse(reports=[ReportListItem(
        id=r.id, brand_name=name, status=r.status.value, scores=visible_scores(r.scores),
        created_at=r.created_at
    ) for r, name in rows], total=total, page=number, page_size=size)


async def read_owned(db, report_id: str, user_id: str):
    report = await owned_report(db, report_id, user_id)
    allowed = set(PUBLIC_REPORT_FIELDS)
    if await has_tier(db, user_id, TierEnum.RADAR):
        allowed.add("meta_ads")
    payload = ({k: v for k, v in report.payload.items() if k in allowed}
               if report.payload is not None else None)
    return ReportResponse(
        id=report.id, user_id=user_id, brand_id=report.brand_id, status=report.status.value,
        payload=payload, scores=visible_scores(report.scores),
        error_message="Analysis failed" if report.error_message else None,
        generated_at=report.generated_at, created_at=report.created_at, expires_at=report.expires_at,
    )


async def delete_owned(db, report_id: str, user_id: str):
    await reports.remove(db, await owned_report(db, report_id, user_id))
    return {"deleted": True}
