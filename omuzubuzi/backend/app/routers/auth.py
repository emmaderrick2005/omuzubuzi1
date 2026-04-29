"""
MOD-01: User Registration & Authentication
FR-01-01 through FR-01-08
- Phone-based OTP registration
- Passwordless login
- JWT session management
- Language toggle (EN / Luganda)
- Rate limiting: max 3 OTP attempts per 10 minutes (NFR 4.2)
"""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from redis.asyncio import Redis

from app.database import get_db
from app.models import User, OTPSession, UserRole, Language
from app.utils.security import (
    hash_otp, verify_otp, hash_pin, verify_pin,
    create_access_token, create_refresh_token, decode_token
)
from app.utils.sms import generate_otp, send_otp

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_RATE_LIMIT_KEY = "otp_rate:{phone}"
OTP_MAX_ATTEMPTS = 3
OTP_WINDOW_SECONDS = 600  # 10 minutes
OTP_EXPIRY_MINUTES = 10


async def get_redis() -> Redis:
    from app.main import redis_client
    return redis_client


# ── Schemas ────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+256\d{9}$", description="Uganda phone: +256XXXXXXXXX")
    name: str = Field(..., min_length=2, max_length=255)
    role: UserRole
    language: Language = Language.EN


class OTPVerifyRequest(BaseModel):
    phone: str
    otp: str = Field(..., min_length=6, max_length=6)
    purpose: str = Field(default="register")


class LoginRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+256\d{9}$")


class PINSetRequest(BaseModel):
    phone: str
    pin: str = Field(..., min_length=4, max_length=6, pattern=r"^\d+$")
    token: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


# ── Helpers ────────────────────────────────────────────────────────────────

async def check_otp_rate_limit(phone: str, redis: Redis) -> None:
    """NFR 4.2: max 3 OTP requests per 10 minutes per phone."""
    key = OTP_RATE_LIMIT_KEY.format(phone=phone)
    count = await redis.get(key)
    if count and int(count) >= OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "en": "Too many OTP requests. Please wait 10 minutes.",
                "lg": "Obulagirizi bungi. Linda eddakiika 10.",
            }
        )
    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, OTP_WINDOW_SECONDS)
    await pipe.execute()


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/register/request-otp", status_code=status.HTTP_200_OK)
async def request_registration_otp(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    FR-01-01, FR-01-02: Register with phone, receive OTP via SMS.
    """
    await check_otp_rate_limit(req.phone, redis)

    # Check if phone already registered
    result = await db.execute(select(User).where(User.phone == req.phone))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered."
        )

    # Store registration intent in Redis (TTL 15 min)
    await redis.setex(
        f"reg_intent:{req.phone}",
        900,
        f"{req.name}|{req.role.value}|{req.language.value}"
    )

    otp = generate_otp()
    otp_hash = hash_otp(otp)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp_session = OTPSession(
        phone=req.phone,
        otp_hash=otp_hash,
        purpose="register",
        expires_at=expires_at,
    )
    db.add(otp_session)

    await send_otp(req.phone, otp, language=req.language.value)

    return {"message": "OTP sent", "expires_in": f"{OTP_EXPIRY_MINUTES} minutes"}


@router.post("/register/verify-otp", status_code=status.HTTP_201_CREATED)
async def verify_registration_otp(
    req: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    FR-01-02: Verify OTP and create user account.
    """
    result = await db.execute(
        select(OTPSession)
        .where(
            OTPSession.phone == req.phone,
            OTPSession.purpose == "register",
            OTPSession.is_used == False,
            OTPSession.expires_at > datetime.now(timezone.utc),
        )
        .order_by(OTPSession.created_at.desc())
        .limit(1)
    )
    otp_session = result.scalar_one_or_none()

    if not otp_session or not verify_otp(req.otp, otp_session.otp_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP."
        )

    otp_session.is_used = True

    # Retrieve registration intent
    intent_raw = await redis.get(f"reg_intent:{req.phone}")
    if not intent_raw:
        raise HTTPException(status_code=400, detail="Registration session expired. Please restart.")

    name, role_str, lang_str = intent_raw.decode().split("|")

    user = User(
        phone=req.phone,
        name=name,
        role=UserRole(role_str),
        language=Language(lang_str),
    )
    db.add(user)
    await db.flush()

    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    await redis.delete(f"reg_intent:{req.phone}")

    return {
        "user_id": str(user.id),
        "role": user.role,
        "language": user.language,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login/request-otp")
async def request_login_otp(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """FR-01-03: Passwordless login — send OTP to registered phone."""
    await check_otp_rate_limit(req.phone, redis)

    result = await db.execute(select(User).where(User.phone == req.phone, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        # Don't reveal whether phone is registered
        return {"message": "If this number is registered, an OTP has been sent."}

    otp = generate_otp()
    otp_hash = hash_otp(otp)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp_session = OTPSession(
        phone=req.phone,
        otp_hash=otp_hash,
        purpose="login",
        expires_at=expires_at,
    )
    db.add(otp_session)

    await send_otp(req.phone, otp, language=user.language.value)

    return {"message": "If this number is registered, an OTP has been sent."}


@router.post("/login/verify-otp")
async def verify_login_otp(
    req: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """FR-01-03: Verify OTP and issue JWT tokens."""
    result = await db.execute(
        select(OTPSession)
        .where(
            OTPSession.phone == req.phone,
            OTPSession.purpose == "login",
            OTPSession.is_used == False,
            OTPSession.expires_at > datetime.now(timezone.utc),
        )
        .order_by(OTPSession.created_at.desc())
        .limit(1)
    )
    otp_session = result.scalar_one_or_none()

    if not otp_session or not verify_otp(req.otp, otp_session.otp_hash):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

    otp_session.is_used = True

    user_result = await db.execute(select(User).where(User.phone == req.phone))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive.")

    return {
        "access_token": create_access_token({"sub": str(user.id), "role": user.role.value}),
        "refresh_token": create_refresh_token({"sub": str(user.id)}),
        "token_type": "bearer",
        "user_id": str(user.id),
        "role": user.role,
        "language": user.language,
    }


@router.post("/token/refresh")
async def refresh_access_token(req: TokenRefreshRequest):
    """FR-01-08: Secure token refresh."""
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    new_access = create_access_token({"sub": payload["sub"], "role": payload.get("role", "buyer")})
    return {"access_token": new_access, "token_type": "bearer"}


@router.post("/pin/set")
async def set_pin(req: PINSetRequest, db: AsyncSession = Depends(get_db)):
    """FR-01-03: Optional PIN setup after OTP verification."""
    try:
        payload = decode_token(req.token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token.")

    result = await db.execute(select(User).where(User.phone == req.phone))
    user = result.scalar_one_or_none()
    if not user or str(user.id) != payload["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden.")

    user.pin_hash = hash_pin(req.pin)
    return {"message": "PIN set successfully."}
