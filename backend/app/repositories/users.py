"""User identity persistence; no authentication decisions live here."""
import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models import User


async def by_id(db, user_id: str):
    return (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()


async def ensure_identity(db, subject: str):
    statement = select(User).where(User.clerk_user_id == subject)
    user = (await db.execute(statement)).scalar_one_or_none()
    if user is not None:
        return user
    try:
        async with db.begin_nested():
            user = User(id=str(uuid.uuid4()), clerk_user_id=subject,
                        email=f"{subject}@identity.brandcompass.invalid")
            db.add(user)
            await db.flush()
        return user
    except IntegrityError:
        user = (await db.execute(statement)).scalar_one_or_none()
        if user is None:
            raise
        return user
