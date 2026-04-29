import uuid, enum
from datetime import datetime
from sqlalchemy import String, DateTime, Float, ForeignKey, Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class VehicleType(str, enum.Enum):
    boda = "boda"       # < 20 kg
    tuktuk = "tuktuk"   # 20–200 kg
    fuso = "fuso"       # > 200 kg

class DeliveryStatus(str, enum.Enum):
    broadcast = "broadcast"
    assigned = "assigned"
    en_route_pickup = "en_route_pickup"
    picked_up = "picked_up"
    in_transit = "in_transit"
    delivered = "delivered"
    failed = "failed"

class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    vehicle_type: Mapped[VehicleType] = mapped_column(SAEnum(VehicleType))
    plate_number: Mapped[str | None] = mapped_column(String(20))
    rating: Mapped[float] = mapped_column(Float, default=5.0)
    total_ratings: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    # Real-time location (updated via WebSocket)
    location_lat: Mapped[float | None] = mapped_column(Float)
    location_lng: Mapped[float | None] = mapped_column(Float)
    location_updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["User"] = relationship("User", back_populates="delivery_profile")

class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), unique=True)
    partner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("delivery_partners.id"))
    vehicle_type: Mapped[VehicleType] = mapped_column(SAEnum(VehicleType))
    status: Mapped[DeliveryStatus] = mapped_column(SAEnum(DeliveryStatus), default=DeliveryStatus.broadcast)
    fee: Mapped[float] = mapped_column(Float, default=0.0)          # UGX
    distance_km: Mapped[float | None] = mapped_column(Float)
    broadcast_expires_at: Mapped[datetime | None] = mapped_column(DateTime)  # 2-min accept window
    pickup_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)

    order: Mapped["Order"] = relationship("Order", back_populates="delivery")
    partner: Mapped["DeliveryPartner"] = relationship("DeliveryPartner")
