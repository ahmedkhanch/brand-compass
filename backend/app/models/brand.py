"""Brand model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    social_accounts: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="brands")
    reports = relationship("Report", back_populates="brand", lazy="selectin")
