"""Shared API authentication dependencies."""
from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.security import bearer_scheme
from app.core.identity import authenticate
from app.services.identity import application_user


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> str:
    return await authenticate(credentials.credentials if credentials else "")


async def get_or_create_user(
    clerk_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await application_user(db, clerk_user_id)
