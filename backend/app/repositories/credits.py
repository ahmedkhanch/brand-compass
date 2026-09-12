"""Credit and subscription persistence for report submission."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Credit


async def credit_for_user(db: AsyncSession, user_id: str) -> Credit | None:
    return (await db.execute(
        select(Credit).where(Credit.user_id == user_id)
    )).scalar_one_or_none()


async def add_credit(db: AsyncSession, credit: Credit) -> Credit:
    db.add(credit)
    await db.flush()
    return credit
