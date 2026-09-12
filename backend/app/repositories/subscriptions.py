"""Subscription reads and customer references for account services."""
from sqlalchemy import select
from app.models import Subscription


async def active_for_user(db, user_id: str):
    return (await db.execute(select(Subscription).where(
        Subscription.user_id == user_id, Subscription.status == "active"
    ))).scalar_one_or_none()


async def set_customer(db, subscription, customer_id):
    subscription.stripe_cust_id = customer_id
    await db.flush()
