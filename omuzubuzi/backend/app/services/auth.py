"""
MOD-01: Authentication service
- Phone OTP via Africa's Talking
- JWT session management
- bcrypt PIN hashing (12 rounds)
"""
import secrets, bcrypt, jwt, httpx
from datetime import datetime, timedelta
from app.config import settings

def hash_pin(pin: str) -> str:
    """bcrypt 12 rounds — FR-01-08 / NFR 4.2"""
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt(rounds=12)).decode()

def verify_pin(pin: str, hashed: str) -> bool:
    return bcrypt.checkpw(pin.encode(), hashed.encode())

def generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)  # 6-digit OTP

def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

async def send_otp_sms(phone: str, otp: str, language: str = "en") -> bool:
    """Send OTP via Africa's Talking SMS API (FR-01-02)"""
    if language == "lg":
        message = f"Omuzubuzi: Koodi yo ey'ekyaama kwe {otp}. Ennaanaga dda mu dakiika 5."
    else:
        message = f"Omuzubuzi: Your OTP code is {otp}. Expires in 5 minutes. Do not share."

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.africastalking.com/version1/messaging",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "apiKey": settings.AT_API_KEY,
                },
                data={
                    "username": settings.AT_USERNAME,
                    "to": phone,
                    "message": message,
                    "from": settings.AT_SENDER_ID,
                },
                timeout=10.0,
            )
            return resp.status_code == 201
    except Exception:
        return False
