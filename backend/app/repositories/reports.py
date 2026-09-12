"""Every report query includes its owning application user."""
from sqlalchemy import select, func
from app.models import Report, Brand


async def owned(db, report_id: str, user_id: str):
    return (await db.execute(select(Report).where(
        Report.id == report_id, Report.user_id == user_id
    ))).scalar_one_or_none()


async def status(db, report_id: str, user_id: str):
    return (await db.execute(select(Report.status).where(
        Report.id == report_id, Report.user_id == user_id
    ))).scalar_one_or_none()


async def page(db, user_id: str, number: int, size: int):
    total = (await db.execute(select(func.count()).select_from(Report).where(
        Report.user_id == user_id
    ))).scalar_one()
    rows = (await db.execute(select(Report, Brand.name).outerjoin(
        Brand, (Brand.id == Report.brand_id) & (Brand.user_id == user_id)
    ).where(Report.user_id == user_id).order_by(Report.created_at.desc(), Report.id.desc())
        .offset((number - 1) * size).limit(size))).all()
    return rows, total


async def remove(db, report):
    await db.delete(report)
    await db.flush()


async def save_ads(db, report, ads: dict):
    report.payload = {**(report.payload or {}), "meta_ads": ads}
    await db.flush()
