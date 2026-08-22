"""ORM model for virtual-tour payments processed through Wompi."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.engine import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TourPaymentORM(Base):
    __tablename__ = "tour_payments"
    __table_args__ = (
        CheckConstraint("entity_type IN ('properties','projects')", name="ck_tour_payments_entity"),
        CheckConstraint("status IN ('pending','approved','declined','voided')", name="ck_tour_payments_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    amount_in_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    reference: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    wompi_transaction_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    tour_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("virtual_tours.id"), nullable=True
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
