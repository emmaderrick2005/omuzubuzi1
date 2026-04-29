import uuid, enum
from datetime import datetime
from sqlalchemy import String, DateTime, Float, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class PaymentMethod(str, enum.Enum):
    mtn_momo = "mtn_momo"
    airtel_money = "airtel_money"
    card = "card"
    cash_on_delivery = "cash_on_delivery"

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    held_in_escrow = "held_in_escrow"
    released = "released"
    refunded = "refunded"
    failed = "failed"

class Payment(Base):
    __tablename__ = "payments"
    # 7-year retention mandatory — URA tax compliance (NFR 6.2)
    # NEVER log financial data fields (NFR 4.2 security)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), unique=True)
    method: Mapped[PaymentMethod] = mapped_column(SAEnum(PaymentMethod))
    amount: Mapped[float] = mapped_column(Float, nullable=False)   # UGX
    status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus), default=PaymentStatus.pending)
    provider_ref: Mapped[str | None] = mapped_column(String(100))   # MoMo transaction ID
    # KYC gate — NPS Act 2020: ID required for txn >= UGX 1,000,000
    requires_id_verification: Mapped[bool] = mapped_column(default=False)
    id_verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    # Escrow timestamps
    escrowed_at: Mapped[datetime | None] = mapped_column(DateTime)
    released_at: Mapped[datetime | None] = mapped_column(DateTime)
    # Receipt
    receipt_url: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # Note: phone_number, account details are NOT stored here — only in provider

    order: Mapped["Order"] = relationship("Order", back_populates="payment")
