"""CachedResult model — brand-level cache with 24h TTL (§10)."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class CachedResult(Base):
    __tablename__ = "cached_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cache_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
