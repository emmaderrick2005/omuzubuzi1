"""
MOD-07: SMS and in-app notification service via Africa's Talking
"""
import httpx
from app.config import settings

SMS_TEMPLATES = {
    "en": {
        "order_placed":    "Omuzubuzi: Order #{order_id} placed. Total: UGX {amount:,}. Track in app.",
        "order_confirmed": "Omuzubuzi: Your order #{order_id} has been confirmed by the wholesaler.",
        "order_picked_up": "Omuzubuzi: Order #{order_id} has been picked up by your rider.",
        "order_delivered": "Omuzubuzi: Order #{order_id} delivered! Rate your experience in the app.",
        "payment_confirmed": "Omuzubuzi: Payment confirmed for order #{order_id}.",
        "low_stock":       "Omuzubuzi: Stock alert — {product} is below {threshold} units.",
    },
    "lg": {
        "order_placed":    "Omuzubuzi: Omulimu #{order_id} guweereddwa. Ssente: UGX {amount:,}.",
        "order_confirmed": "Omuzubuzi: Omulimu #{order_id} gukkiriziddwa omuzubuzi.",
        "order_picked_up": "Omuzubuzi: Omulimu #{order_id} gutwaliddwa.",
        "order_delivered": "Omuzubuzi: Omulimu #{order_id} gutuukiridde! Weereza mu app.",
        "payment_confirmed": "Omuzubuzi: Ssente z'omulimu #{order_id} zakkirizibwa.",
        "low_stock":       "Omuzubuzi: Ebintu {product} biri wansi wa {threshold}.",
    },
}

async def send_sms(phone: str, event: str, lang: str = "en", **kwargs) -> bool:
    """FR-07-01: SMS for order lifecycle events"""
    template = SMS_TEMPLATES.get(lang, SMS_TEMPLATES["en"]).get(event, "")
    if not template:
        return False
    message = template.format(**kwargs)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.africastalking.com/version1/messaging",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "apiKey": settings.AT_API_KEY,
                },
                data={"username": settings.AT_USERNAME, "to": phone, "message": message, "from": settings.AT_SENDER_ID},
                timeout=10.0,
            )
        return resp.status_code == 201
    except Exception:
        return False
