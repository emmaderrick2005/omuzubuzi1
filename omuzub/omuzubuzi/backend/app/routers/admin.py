"""MOD-08: Admin dashboard and reporting"""
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.wholesaler import Wholesaler, KYCStatus
from app.models.order import Order
from app.utils.auth import require_role

router = APIRouter()

class KYCDecisionRequest(BaseModel):
    decision: str  # "approved" or "rejected"
    reason: Optional[str] = None

@router.get("/dashboard")
async def admin_dashboard(
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("admin")),
):
    """FR-08-01: Platform metrics"""
    user_count = await db.scalar(select(func.count(User.id)))
    order_count = await db.scalar(select(func.count(Order.id)))
    pending_kyc = await db.scalar(
        select(func.count(Wholesaler.id)).where(Wholesaler.kyc_status == KYCStatus.pending)
    )
    return {
        "total_users": user_count,
        "total_orders": order_count,
        "pending_kyc": pending_kyc,
        "platform": "Omuzubuzi v1.0",
    }

@router.post("/kyc/{wholesaler_id}")
async def decide_kyc(
    wholesaler_id: uuid.UUID,
    req: KYCDecisionRequest,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("admin")),
):
    """FR-08-02: Approve or reject KYC"""
    result = await db.execute(select(Wholesaler).where(Wholesaler.id == wholesaler_id))
    w = result.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="Wholesaler not found")
    w.kyc_status = KYCStatus(req.decision)
    w.kyc_rejection_reason = req.reason
    w.is_verified_badge = req.decision == "approved"
    return {"message": f"KYC {req.decision} for {wholesaler_id}"}

@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("admin")),
):
    """FR-08-03: Suspend user with audit trail"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    return {"message": f"User {user_id} suspended", "suspended_by": user_data["sub"]}
