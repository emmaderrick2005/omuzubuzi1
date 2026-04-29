import uuid, enum
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class UserRole(str, enum.Enum):
    buyer = "buyer"
    wholesaler = "wholesaler"
    delivery_partner = "delivery_partner"
    admin = "admin"

class Language(str, enum.Enum):
    english = "en"
    luganda = "lg"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(120))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False)
    language: Mapped[Language] = mapped_column(SAEnum(Language), default=Language.english)
    pin_hash: Mapped[str | None] = mapped_column(String(72))  # bcrypt 12 rounds
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    # KYC for NPS Act 2020 compliance
    id_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    id_document_url: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    wholesaler_profile: Mapped["Wholesaler"] = relationship("Wholesaler", back_populates="user", uselist=False)
    delivery_profile: Mapped["DeliveryPartner"] = relationship("DeliveryPartner", back_populates="user", uselist=False)
