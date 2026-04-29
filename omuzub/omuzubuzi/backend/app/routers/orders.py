"""MOD-04: Buyer shopping and orders"""
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.models.order import Order, OrderStatus, OrderItem
from app.models.product import Product
from app.models.delivery import Delivery, VehicleType, DeliveryStatus
from app.services.delivery import classify_vehicle, calculate_delivery_fee, haversine_distance
from app.services.notifications import send_sms
from app.utils.auth import get_current_user

router = APIRouter()

class OrderItemSchema(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(..., ge=1)

class PlaceOrderRequest(BaseModel):
    wholesaler_id: uuid.UUID
    items: list[OrderItemSchema]
    delivery_address: str
    delivery_lat: Optional[float] = None
    delivery_lng: Optional[float] = None
    total_weight_kg: float = Field(5.0, description="Estimated weight for vehicle classification")
    notes: Optional[str] = None

@router.post("/", status_code=201)
async def place_order(
    req: PlaceOrderRequest,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user),
):
    """FR-04-02 to FR-04-05: Place a multi-item order"""
    total = 0.0
    order_items = []

    for item in req.items:
        result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = result.scalar_one_or_none()
        if not product or product.is_out_of_stock:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} unavailable")
        if item.quantity < product.moq:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum order for {product.name} is {product.moq} {product.unit}"
            )
        unit_price = product.base_price
        subtotal = unit_price * item.quantity
        total += subtotal
        order_items.append((product, item.quantity, unit_price, subtotal))

    # Determine vehicle and delivery fee (FR-06-01 / FR-04-04)
    vehicle = classify_vehicle(req.total_weight_kg)
    # Default distance if no coords (estimate 5km for Kampala)
    distance = 5.0
    delivery_fee = calculate_delivery_fee(distance, vehicle)

    order = Order(
        buyer_id=uuid.UUID(user_data["sub"]),
        wholesaler_id=req.wholesaler_id,
        total_amount=total,
        delivery_fee=delivery_fee,
        delivery_address=req.delivery_address,
        delivery_lat=req.delivery_lat,
        delivery_lng=req.delivery_lng,
        delivery_type=vehicle.value,
        notes=req.notes,
        can_cancel_until=datetime.utcnow() + timedelta(minutes=10),  # FR-04-09
    )
    db.add(order)
    await db.flush()

    for product, qty, unit_price, subtotal in order_items:
        db.add(OrderItem(order_id=order.id, product_id=product.id, quantity=qty, unit_price=unit_price, subtotal=subtotal))

    # Create delivery broadcast record
    delivery = Delivery(order_id=order.id, vehicle_type=vehicle, fee=delivery_fee, status=DeliveryStatus.broadcast)
    db.add(delivery)

    return {"order_id": str(order.id), "total": total, "delivery_fee": delivery_fee, "vehicle_type": vehicle}


@router.get("/{order_id}/track")
async def track_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user),
):
    """FR-04-06: Real-time order tracking"""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    delivery_result = await db.execute(select(Delivery).where(Delivery.order_id == order_id))
    delivery = delivery_result.scalar_one_or_none()

    return {
        "order_id": str(order.id),
        "status": order.status,
        "delivery_type": order.delivery_type,
        "delivery_status": delivery.status if delivery else None,
        "placed_at": order.placed_at,
        "confirmed_at": order.confirmed_at,
    }


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user),
):
    """FR-04-09: Cancel within 10 minutes if not yet accepted"""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(order.buyer_id) != user_data["sub"]:
        raise HTTPException(status_code=403, detail="Not your order")
    if datetime.utcnow() > order.can_cancel_until:
        raise HTTPException(status_code=400, detail="Cancellation window has closed (10 minutes)")
    if order.status not in (OrderStatus.pending,):
        raise HTTPException(status_code=400, detail=f"Cannot cancel order in status: {order.status}")

    order.status = OrderStatus.cancelled
    return {"message": "Order cancelled successfully"}
