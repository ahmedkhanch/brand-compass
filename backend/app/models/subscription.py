"""Subscription model — Stripe-managed. Tier names from product brief."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
import enum


class TierEnum(str, enum.Enum):
    BOUSSOLE = "boussole"
    RADAR = "radar"
    STRATEGE = "stratege"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    stripe_cust_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_sub_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    tier: Mapped[TierEnum] = mapped_column(Enum(TierEnum), nullable=False, default=TierEnum.BOUSSOLE)
    status: Mapped[str] = mapped_column(String(50), default="active")
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user = relationship("User", back_populates="subscriptions")
