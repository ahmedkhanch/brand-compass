"""Resolve a verified external subject to the application identity."""
from app.repositories import users


async def application_user(db, subject: str) -> dict:
    user = await users.ensure_identity(db, subject)
    return {"user_id": user.id, "clerk_user_id": user.clerk_user_id}
