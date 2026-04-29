"""MOD-02: Wholesaler management"""
import uuid
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.models.wholesaler import Wholesaler, KYCStatus
from app.models.user import User
from app.utils.auth import get_current_user, require_role

router = APIRouter()

class WholesalerProfileRequest(BaseModel):
    business_name: str
    tin: Optional[str] = None
    districts_served: list[str] = []
    address: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None

@router.post("/profile", status_code=201)
async def create_wholesaler_profile(
    req: WholesalerProfileRequest,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("wholesaler")),
):
    wholesaler = Wholesaler(
        user_id=user_data["sub"],
        business_name=req.business_name,
        tin=req.tin,
        districts_served=req.districts_served,
        address=req.address,
        location_lat=req.location_lat,
        location_lng=req.location_lng,
    )
    db.add(wholesaler)
    return {"message": "Profile created. Pending KYC approval."}

@router.get("/dashboard")
async def wholesaler_dashboard(
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("wholesaler")),
):
    """FR-02-01: Dashboard metrics"""
    result = await db.execute(select(Wholesaler).where(Wholesaler.user_id == user_data["sub"]))
    w = result.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="Wholesaler profile not found")
    # TODO: Aggregate from orders table
    return {"wholesaler_id": str(w.id), "business_name": w.business_name, "kyc_status": w.kyc_status, "rating": w.rating}

@router.patch("/hours")
async def update_hours(
    is_open: bool,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("wholesaler")),
):
    """FR-02-04: Open/close store"""
    result = await db.execute(select(Wholesaler).where(Wholesaler.user_id == user_data["sub"]))
    w = result.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="Not found")
    w.is_open = is_open
    return {"is_open": is_open}
