import uuid, enum
from datetime import datetime
from sqlalchemy import String, DateTime, Float, Boolean, ForeignKey, Enum as SAEnum, ARRAY, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class KYCStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class Wholesaler(Base):
    __tablename__ = "wholesalers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    tin: Mapped[str | None] = mapped_column(String(20))           # URA Tax ID
    business_cert_url: Mapped[str | None] = mapped_column(String(512))
    kyc_status: Mapped[KYCStatus] = mapped_column(SAEnum(KYCStatus), default=KYCStatus.pending)
    kyc_rejection_reason: Mapped[str | None] = mapped_column(Text)
    districts_served: Mapped[list | None] = mapped_column(ARRAY(String))
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_ratings: Mapped[int] = mapped_column(default=0)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified_badge: Mapped[bool] = mapped_column(Boolean, default=False)
    location_lat: Mapped[float | None] = mapped_column(Float)
    location_lng: Mapped[float | None] = mapped_column(Float)
    address: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="wholesaler_profile")
    products: Mapped[list["Product"]] = relationship("Product", back_populates="wholesaler")
