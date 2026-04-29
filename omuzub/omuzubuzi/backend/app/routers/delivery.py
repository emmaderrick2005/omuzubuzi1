"""MOD-06: Delivery management"""
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.delivery import Delivery, DeliveryPartner, DeliveryStatus, VehicleType
from app.utils.auth import get_current_user, require_role

router = APIRouter()

class LocationUpdate(BaseModel):
    lat: float
    lng: float

@router.get("/available")
async def available_jobs(
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("delivery_partner")),
):
    """FR-06-02: Available jobs for this delivery partner's vehicle type"""
    partner_result = await db.execute(
        select(DeliveryPartner).where(DeliveryPartner.user_id == user_data["sub"])
    )
    partner = partner_result.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail="Delivery partner profile not found")

    result = await db.execute(
        select(Delivery).where(
            Delivery.status == DeliveryStatus.broadcast,
            Delivery.vehicle_type == partner.vehicle_type,
        ).limit(10)
    )
    return {"jobs": result.scalars().all()}


@router.post("/{delivery_id}/accept")
async def accept_job(
    delivery_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("delivery_partner")),
):
    """FR-06-03: Accept job within 2-minute window"""
    result = await db.execute(select(Delivery).where(Delivery.id == delivery_id))
    delivery = result.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status_code=404, detail="Job not found")
    if delivery.status != DeliveryStatus.broadcast:
        raise HTTPException(status_code=409, detail="Job already taken")

    partner_result = await db.execute(
        select(DeliveryPartner).where(DeliveryPartner.user_id == user_data["sub"])
    )
    partner = partner_result.scalar_one_or_none()
    delivery.partner_id = partner.id
    delivery.status = DeliveryStatus.assigned
    return {"message": "Job accepted. Proceed to wholesaler for pickup."}


@router.post("/{delivery_id}/confirm-pickup")
async def confirm_pickup(
    delivery_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("delivery_partner")),
):
    """FR-06-07: Confirm pickup from wholesaler"""
    result = await db.execute(select(Delivery).where(Delivery.id == delivery_id))
    delivery = result.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status_code=404, detail="Not found")
    delivery.status = DeliveryStatus.picked_up
    delivery.pickup_confirmed_at = datetime.utcnow()
    return {"message": "Pickup confirmed"}


@router.post("/{delivery_id}/confirm-delivery")
async def confirm_delivery(
    delivery_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("delivery_partner")),
):
    """FR-06-07: Confirm delivery to buyer"""
    result = await db.execute(select(Delivery).where(Delivery.id == delivery_id))
    delivery = result.scalar_one_or_none()
    delivery.status = DeliveryStatus.delivered
    delivery.delivered_at = datetime.utcnow()
    return {"message": "Delivery confirmed"}


@router.patch("/location")
async def update_location(
    loc: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(require_role("delivery_partner")),
):
    """Real-time location update for tracking (FR-06-05)"""
    result = await db.execute(
        select(DeliveryPartner).where(DeliveryPartner.user_id == user_data["sub"])
    )
    partner = result.scalar_one_or_none()
    if partner:
        partner.location_lat = loc.lat
        partner.location_lng = loc.lng
        partner.location_updated_at = datetime.utcnow()
    return {"status": "updated"}
