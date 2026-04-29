"""
MOD-05: Payment processing router
- MTN MoMo + Airtel Money
- CRITICAL: NPS Act 2020 ID verification gate >= UGX 1,000,000
- Escrow logic
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.services.payments import (
    requires_id_verification, initiate_mtn_momo, initiate_airtel_money
)
from app.services.notifications import send_sms
from app.utils.auth import get_current_user

router = APIRouter()

class PaymentInitRequest(BaseModel):
    order_id: uuid.UUID
    method: PaymentMethod
    phone: str  # MoMo number — NOT logged, not stored long-term

class WebhookPayload(BaseModel):
    reference_id: str
    status: str
    provider: str

@router.post("/initiate")
async def initiate_payment(
    req: PaymentInitRequest,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user),
):
    """
    FR-05-01 / FR-05-02: Initiate MoMo or Airtel payment.
    CRITICAL (NPS Act 2020): Block if amount >= UGX 1,000,000 and user not ID-verified.
    """
    # Load order
    result = await db.execute(select(Order).where(Order.id == req.order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(order.buyer_id) != user_data["sub"]:
        raise HTTPException(status_code=403, detail="Not your order")

    # ─── REGULATORY GATE: NPS Act 2020 ───────────────────────────────────────
    if requires_id_verification(order.total_amount):
        # Load user to check ID verification status
        user_result = await db.execute(select(User).where(User.id == order.buyer_id))
        user = user_result.scalar_one_or_none()
        if not user or not user.id_verified:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "ID_VERIFICATION_REQUIRED",
                    "message": (
                        "Transactions of UGX 1,000,000 or more require identity "
                        "verification under the National Payment Systems Act 2020. "
                        "Please complete ID verification in your profile."
                    ),
                    "threshold_ugx": 1_000_000,
                }
            )
    # ─────────────────────────────────────────────────────────────────────────

    # Create payment record
    payment = Payment(
        order_id=order.id,
        method=req.method,
        amount=order.total_amount,
        status=PaymentStatus.processing,
        requires_id_verification=requires_id_verification(order.total_amount),
    )
    db.add(payment)
    await db.flush()

    # Dispatch to appropriate provider
    if req.method == PaymentMethod.mtn_momo:
        result = await initiate_mtn_momo(req.phone, order.total_amount, str(order.id))
    elif req.method == PaymentMethod.airtel_money:
        result = await initiate_airtel_money(req.phone, order.total_amount, str(order.id))
    else:
        raise HTTPException(status_code=400, detail="Unsupported payment method")

    if not result.get("accepted"):
        payment.status = PaymentStatus.failed
        raise HTTPException(status_code=502, detail="Payment provider rejected request")

    payment.provider_ref = result.get("reference_id")
    payment.status = PaymentStatus.held_in_escrow
    payment.escrowed_at = datetime.utcnow()

    return {
        "payment_id": str(payment.id),
        "reference_id": payment.provider_ref,
        "status": "processing",
        "message": "Check your phone to approve the MoMo request",
    }


@router.post("/webhook/{provider}")
async def payment_webhook(
    provider: str,
    payload: WebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    """Handle MoMo / Airtel payment callbacks — release escrow on success"""
    result = await db.execute(
        select(Payment).where(Payment.provider_ref == payload.reference_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        return {"status": "ignored"}

    if payload.status in ("SUCCESSFUL", "SUCCESS"):
        payment.status = PaymentStatus.released
        payment.released_at = datetime.utcnow()

        # Update order status
        order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
        order = order_result.scalar_one_or_none()
        if order:
            order.status = OrderStatus.confirmed
            order.confirmed_at = datetime.utcnow()

    elif payload.status in ("FAILED", "TIMEOUT", "REJECTED"):
        payment.status = PaymentStatus.failed

    return {"status": "processed"}


@router.post("/{payment_id}/refund")
async def refund_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user),
):
    """FR-05-06: Refund within 24 hours"""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.status = PaymentStatus.refunded
    return {"message": "Refund initiated — funds will return to original payment method within 24h"}
