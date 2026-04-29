import uuid, enum
from datetime import datetime
from sqlalchemy import String, DateTime, Float, Integer, ForeignKey, Enum as SAEnum, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    packed = "packed"
    picked_up = "picked_up"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"
    disputed = "disputed"
    refunded = "refunded"

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"))
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)  # UGX — price at time of order
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="items")

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    wholesaler_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wholesalers.id"))
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), default=OrderStatus.pending)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)  # UGX
    delivery_fee: Mapped[float] = mapped_column(Float, default=0.0)
    platform_commission: Mapped[float] = mapped_column(Float, default=0.0)
    delivery_address: Mapped[str] = mapped_column(String(500))
    delivery_lat: Mapped[float | None]
    delivery_lng: Mapped[float | None]
    delivery_type: Mapped[str | None] = mapped_column(String(20))   # boda / tuktuk / fuso
    notes: Mapped[str | None] = mapped_column(Text)
    # Cancellation window: 10 min from placement if not yet accepted
    can_cancel_until: Mapped[datetime | None] = mapped_column(DateTime)
    placed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
    # 7-year retention — soft delete only, never hard delete (URA compliance)
    is_archived: Mapped[bool] = mapped_column(default=False)

    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment: Mapped["Payment"] = relationship("Payment", back_populates="order", uselist=False)
    delivery: Mapped["Delivery"] = relationship("Delivery", back_populates="order", uselist=False)
