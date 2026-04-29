"""
Core database models for Omuzubuzi B2B Wholesale Marketplace
Entities from SRS Section 6.1
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    String, Integer, BigInteger, Boolean, DateTime, Text,
    Numeric, ForeignKey, Enum, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.sql import func
from app.database import Base


# ── Enums ──────────────────────────────────────────────────────────────────

class UserRole(str, PyEnum):
    BUYER = "buyer"
    WHOLESALER = "wholesaler"
    DELIVERY_PARTNER = "delivery_partner"
    ADMIN = "admin"


class Language(str, PyEnum):
    EN = "en"
    LG = "lg"  # Luganda


class KYCStatus(str, PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class OrderStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PACKED = "packed"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class PaymentMethod(str, PyEnum):
    MTN_MOMO = "mtn_momo"
    AIRTEL_MONEY = "airtel_money"
    CARD = "card"
    CASH_ON_DELIVERY = "cash_on_delivery"


class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    ESCROW = "escrow"         # held until delivery confirmed
    RELEASED = "released"     # disbursed to wholesaler
    REFUNDED = "refunded"
    FAILED = "failed"


class DeliveryVehicle(str, PyEnum):
    BODA = "boda"        # < 20 kg
    TUK_TUK = "tuk_tuk" # 20–200 kg
    FUSO = "fuso"        # > 200 kg


class ProductCategory(str, PyEnum):
    GROCERIES = "groceries"
    BEVERAGES = "beverages"
    PERSONAL_CARE = "personal_care"
    HOUSEHOLD = "household"
    STATIONERY = "stationery"
    ELECTRONICS = "electronics"
    AGRI_PRODUCE = "agri_produce"
    OTHER = "other"


class ProductUnit(str, PyEnum):
    KG = "kg"
    LITRE = "litre"
    PIECE = "piece"
    BOX = "box"
    SACK = "sack"


# ── Models ─────────────────────────────────────────────────────────────────

class User(Base):
    """
    MOD-01: Core user entity.
    Phone is the primary identifier (FR-01-01).
    Language preference per FR-01-06.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    language: Mapped[Language] = mapped_column(Enum(Language), default=Language.EN)
    pin_hash: Mapped[str | None] = mapped_column(String(255))  # bcrypt 12 rounds
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    id_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # NPS Act compliance
    national_id: Mapped[str | None] = mapped_column(String(50))        # encrypted at rest
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    wholesaler_profile = relationship("Wholesaler", back_populates="user", uselist=False)
    delivery_partner_profile = relationship("DeliveryPartner", back_populates="user", uselist=False)


class Wholesaler(Base):
    """MOD-02: Wholesaler profile and KYC."""
    __tablename__ = "wholesalers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tin: Mapped[str] = mapped_column(String(50), nullable=False)  # URA TIN — FR-01-04
    district: Mapped[str] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)
    kyc_status: Mapped[KYCStatus] = mapped_column(Enum(KYCStatus), default=KYCStatus.PENDING)
    kyc_document_url: Mapped[str | None] = mapped_column(String(500))  # S3 URL
    kyc_rejection_reason: Mapped[str | None] = mapped_column(Text)
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    moq_global: Mapped[int | None] = mapped_column(Integer)  # store-wide MOQ
    commission_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.05)  # 5% default
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="wholesaler_profile")
    products = relationship("Product", back_populates="wholesaler")


class Product(Base):
    """
    MOD-03: Product catalog with MOQ and bulk price tiers.
    FR-03-01, FR-03-05 (price tiers as JSON).
    """
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wholesaler_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wholesalers.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)  # ETA 2011 §24(1)(h)
    category: Mapped[ProductCategory] = mapped_column(Enum(ProductCategory), nullable=False)
    unit: Mapped[ProductUnit] = mapped_column(Enum(ProductUnit), nullable=False)
    base_price: Mapped[int] = mapped_column(BigInteger, nullable=False)  # UGX, stored as integer
    moq: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    stock_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_out_of_stock: Mapped[bool] = mapped_column(Boolean, default=False)
    images: Mapped[list] = mapped_column(JSON, default=list)  # list of S3 URLs
    # Bulk price tiers: [{"min_qty": 10, "max_qty": 50, "price": 500}, ...]
    price_tiers: Mapped[list] = mapped_column(JSON, default=list)
    # Promotional discount
    discount_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    discount_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    wholesaler = relationship("Wholesaler", back_populates="products")

    __table_args__ = (
        Index("ix_products_category_active", "category", "is_active"),
        Index("ix_products_wholesaler_active", "wholesaler_id", "is_active"),
    )


class Order(Base):
    """MOD-04: Buyer orders. Supports multi-vendor (items JSON)."""
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    wholesaler_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wholesalers.id"), index=True)
    items: Mapped[list] = mapped_column(JSON, nullable=False)  # [{product_id, name, qty, unit_price, subtotal}]
    total_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # UGX
    delivery_fee: Mapped[int] = mapped_column(BigInteger, default=0)
    delivery_type: Mapped[DeliveryVehicle | None] = mapped_column(Enum(DeliveryVehicle))
    delivery_address: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    delivery_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    # Audit trail for Electronic Transactions Act 2011
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # URA 7-year retention — do NOT hard delete; set is_archived flag
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    payment = relationship("Payment", back_populates="order", uselist=False)
    delivery = relationship("Delivery", back_populates="order", uselist=False)


class Payment(Base):
    """
    MOD-05: Payment records.
    CRITICAL: financial data must never appear in logs (NFR 4.2).
    Escrow model: ESCROW → RELEASED after delivery confirmation.
    NPS Act: ID check gate for amounts >= 1,000,000 UGX.
    """
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), unique=True)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # UGX
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    provider_ref: Mapped[str | None] = mapped_column(String(255))  # MTN/Airtel transaction ID
    # NPS Act compliance gate
    id_verification_required: Mapped[bool] = mapped_column(Boolean, default=False)
    id_verification_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    receipt_url: Mapped[str | None] = mapped_column(String(500))  # S3 URL for digital receipt
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # URA 7-year retention
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    order = relationship("Order", back_populates="payment")


class DeliveryPartner(Base):
    """MOD-06: Delivery partner profile with vehicle type and live location."""
    __tablename__ = "delivery_partners"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    vehicle_type: Mapped[DeliveryVehicle] = mapped_column(Enum(DeliveryVehicle), nullable=False)
    plate_number: Mapped[str] = mapped_column(String(20), nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=5.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    location_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    location_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    is_available: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # suspended if rating < 3.0
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="delivery_partner_profile")


class Delivery(Base):
    """MOD-06: Delivery job tracking."""
    __tablename__ = "deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), unique=True)
    partner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("delivery_partners.id"))
    vehicle_type: Mapped[DeliveryVehicle] = mapped_column(Enum(DeliveryVehicle), nullable=False)
    pickup_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="unassigned")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="delivery")


class OTPSession(Base):
    """
    MOD-01: One-time password sessions for phone verification.
    Rate-limited: max 3 per 10 minutes per phone (NFR 4.2).
    """
    __tablename__ = "otp_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # OTP code stored hashed — never plaintext
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(50))  # "register" | "login" | "payment_verify"
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    """
    Security audit trail — Computer Misuse Act 2011.
    FR-08-08: breach notification log.
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[str | None] = mapped_column(String(100))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
