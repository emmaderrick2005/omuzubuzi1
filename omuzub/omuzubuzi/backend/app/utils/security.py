"""
JWT session management and bcrypt hashing.
NFR 4.2: bcrypt minimum 12 rounds.
FR-01-08: JWT-based session management with secure token refresh.
"""
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.config import get_settings

settings = get_settings()

# bcrypt 12 rounds — NFR 4.2
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_pin(pin: str) -> str:
    return pwd_context.hash(pin)


def verify_pin(pin: str, hashed: str) -> bool:
    return pwd_context.verify(pin, hashed)


def hash_otp(otp: str) -> str:
    """OTP codes are also hashed before storage."""
    return pwd_context.hash(otp)


def verify_otp(otp: str, hashed: str) -> bool:
    return pwd_context.verify(otp, hashed)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire, "type": "access"})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload.update({"exp": expire, "type": "refresh"})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise ValueError("Invalid or expired token")
