import uuid, enum
from datetime import datetime
from sqlalchemy import String, DateTime, Float, Integer, ForeignKey, Enum as SAEnum, ARRAY, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class ProductCategory(str, enum.Enum):
    groceries = "Groceries"
    beverages = "Beverages"
    personal_care = "Personal Care"
    household = "Household"
    stationery = "Stationery"
    electronics = "Electronics"
    agri_produce = "Agri-produce"
    other = "Other"

class PriceTier(Base):
    """Bulk price tiers: e.g. 10-50 units @ 500, 51-200 units @ 450"""
    __tablename__ = "price_tiers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    min_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    max_qty: Mapped[int | None] = mapped_column(Integer)   # None = unlimited
    price_per_unit: Mapped[float] = mapped_column(Float, nullable=False)  # UGX

    product: Mapped["Product"] = relationship("Product", back_populates="price_tiers")

class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wholesaler_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wholesalers.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    name_lg: Mapped[str | None] = mapped_column(String(200))     # Luganda name
    category: Mapped[ProductCategory] = mapped_column(SAEnum(ProductCategory))
    description: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String(30))                # kg / litre / piece / box / sack
    base_price: Mapped[float] = mapped_column(Float, nullable=False)   # UGX base price
    moq: Mapped[int] = mapped_column(Integer, default=1)         # Minimum Order Quantity
    stock_qty: Mapped[int] = mapped_column(Integer, default=0)
    is_out_of_stock: Mapped[bool] = mapped_column(Boolean, default=False)
    images: Mapped[list | None] = mapped_column(ARRAY(String))   # S3 URLs
    sku: Mapped[str | None] = mapped_column(String(50), unique=True)
    barcode: Mapped[str | None] = mapped_column(String(50))
    # Promotions
    discount_pct: Mapped[float | None] = mapped_column(Float)
    discount_expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    wholesaler: Mapped["Wholesaler"] = relationship("Wholesaler", back_populates="products")
    price_tiers: Mapped[list["PriceTier"]] = relationship("PriceTier", back_populates="product", cascade="all, delete-orphan")
