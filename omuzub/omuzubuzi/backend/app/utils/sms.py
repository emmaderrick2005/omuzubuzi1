"""
Africa's Talking SMS integration — FR-01-02 (OTP), FR-07-01 (notifications).
Uganda-optimised gateway.
"""
import random
import string
import httpx
from app.config import get_settings

settings = get_settings()

AT_SMS_URL = "https://api.africastalking.com/version1/messaging"


async def send_sms(phone: str, message: str) -> dict:
    """Send SMS via Africa's Talking API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            AT_SMS_URL,
            headers={
                "ApiKey": settings.AT_API_KEY,
                "Accept": "application/json",
            },
            data={
                "username": settings.AT_USERNAME,
                "to": phone,
                "message": message,
                "from": settings.AT_SENDER_ID,
            },
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()


def generate_otp(length: int = 6) -> str:
    """Generate numeric OTP."""
    return "".join(random.choices(string.digits, k=length))


async def send_otp(phone: str, otp: str, language: str = "en") -> dict:
    """
    Send OTP with language-aware message.
    FR-01-06: Luganda and English support.
    """
    messages = {
        "en": f"Your Omuzubuzi verification code is {otp}. Valid for 10 minutes. Do not share.",
        "lg": f"Akabonero ko ka Omuzubuzi kwe {otp}. Kiguma eddakiika 10. Togabana na muntu.",
    }
    msg = messages.get(language, messages["en"])
    return await send_sms(phone, msg)


async def send_order_sms(phone: str, order_id: str, status: str, language: str = "en") -> dict:
    """FR-07-01: Order lifecycle SMS notifications."""
    status_msgs = {
        "en": {
            "confirmed": f"Omuzubuzi: Order #{order_id[:8]} confirmed! Your goods are being prepared.",
            "picked_up": f"Omuzubuzi: Order #{order_id[:8]} picked up. Delivery partner is on the way.",
            "delivered": f"Omuzubuzi: Order #{order_id[:8]} delivered. Thank you for shopping with us!",
        },
        "lg": {
            "confirmed": f"Omuzubuzi: Ogulawo #{order_id[:8]} ekakasizibwa! Ebintu byo bitegekebwa.",
            "picked_up": f"Omuzubuzi: Ogulawo #{order_id[:8]} ogutwala. Omuwasa wa delivery agenda.",
            "delivered": f"Omuzubuzi: Ogulawo #{order_id[:8]} wafiika. Webale okugula naaffe!",
        },
    }
    lang = language if language in status_msgs else "en"
    msg = status_msgs[lang].get(status, f"Omuzubuzi: Order #{order_id[:8]} status: {status}")
    return await send_sms(phone, msg)
