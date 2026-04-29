"""
MOD-03: Product Catalog router
FR-03-01 to FR-03-07
"""
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.product import Product, ProductCategory, PriceTier
from app.models.wholesaler import Wholesaler, KYCStatus
from app.utils.auth import get_current_user, require_role

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────
class PriceTierSchema(BaseModel):
    min_qty: int
    max_qty: Optional[int] = None
    price_per_unit: float  # UGX

class CreateProductRequest(BaseModel):
    name: str = Field(..., max_length=200)
    name_lg: Optional[str] = None  # Luganda name
    category: ProductCategory
    description: Optional[str] = None
    unit: str = Field(..., description="kg / litre / piece / box / sack")
    base_price: float = Field(..., gt=0, description="Price in UGX")
    moq: int = Field(1, ge=1, description="Minimum Order Quantity — FR-03-01")
    stock_qty: int = Field(0, ge=0)
    price_tiers: list[PriceTierSchema] = Field(default=[], description="Bulk pricing tiers — FR-03-05")

class UpdateStockRequest(BaseModel):
    stock_qty: int = Field(..., ge=0)

class PromotionRequest(BaseModel):
    discount_pct: float = Field(..., gt=0, le=100)
    expires_at: datetime

# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/")
async def list_products(
    q: Optional[str] = Query(None, description="Search by name"),
    category: Optional[ProductCategory] = None,
    wholesaler_id: Optional[uuid.UUID] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = True,
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """FR-03-06: Product search with filters"""
    filters = [Product.is_active == True]
    if in_stock_only:
        filters.append(Product.is_out_of_stock == False)
    if q:
        filters.append(or_(
            Product.name.ilike(f"%{q}%"),
            Product.name_lg.ilike(f"%{q}%"),
        ))
    if category:
        filters.append(Product.category == category)
    if wholesaler_id:
        filters.append(Product.wholesaler_id == wholesaler_id)
    if min_price:
        filters.append(Product.base_price >= min_price)
    if max_price:
        filters.append(Product.base_price <= max_price)

    result = await db.execute(
        select(Product).where(and_(*filters)).offset(offset).limit(limit)
    )
    products = result.scalars().all()
    return {"products": products, "total": len(products), "offset": offset}


@router.post("/", status_code=201)
async def create_product(
    req: CreateProductRequest,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("wholesaler")),
):
    """FR-03-01: Create product listing"""
    # Get wholesaler profile
    result = await db.execute(
        select(Wholesaler).where(Wholesaler.user_id == user_data["sub"])
    )
    wholesaler = result.scalar_one_or_none()
    if not wholesaler:
        raise HTTPException(status_code=404, detail="Wholesaler profile not found")
    if wholesaler.kyc_status != KYCStatus.approved:
        raise HTTPException(status_code=403, detail="KYC approval required to list products")

    product = Product(
        wholesaler_id=wholesaler.id,
        name=req.name,
        name_lg=req.name_lg,
        category=req.category,
        description=req.description,
        unit=req.unit,
        base_price=req.base_price,
        moq=req.moq,
        stock_qty=req.stock_qty,
        is_out_of_stock=(req.stock_qty == 0),
    )
    db.add(product)
    await db.flush()

    # Bulk price tiers (FR-03-05)
    for tier in req.price_tiers:
        db.add(PriceTier(
            product_id=product.id,
            min_qty=tier.min_qty,
            max_qty=tier.max_qty,
            price_per_unit=tier.price_per_unit,
        ))

    return {"product_id": str(product.id), "message": "Product listed successfully"}


@router.patch("/{product_id}/stock")
async def update_stock(
    product_id: uuid.UUID,
    req: UpdateStockRequest,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("wholesaler")),
):
    """FR-03-03 / FR-03-04: Update stock, auto-mark out-of-stock"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.stock_qty = req.stock_qty
    product.is_out_of_stock = req.stock_qty == 0  # FR-03-04: auto-mark
    return {"stock_qty": req.stock_qty, "is_out_of_stock": product.is_out_of_stock}


@router.post("/{product_id}/promotion")
async def set_promotion(
    product_id: uuid.UUID,
    req: PromotionRequest,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("wholesaler")),
):
    """FR-03-07: Set promotional discount with expiry"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.discount_pct = req.discount_pct
    product.discount_expires_at = req.expires_at
    return {"message": f"{req.discount_pct}% discount set until {req.expires_at}"}


def get_price_for_quantity(product: Product, qty: int) -> float:
    """Apply bulk pricing tier if applicable"""
    for tier in sorted(product.price_tiers, key=lambda t: t.min_qty, reverse=True):
        if qty >= tier.min_qty and (tier.max_qty is None or qty <= tier.max_qty):
            return tier.price_per_unit
    return product.base_price
