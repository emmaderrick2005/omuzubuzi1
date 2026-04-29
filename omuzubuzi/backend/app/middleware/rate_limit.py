"""
Rate limiting — OTP endpoints: max 3 attempts / 10 min (NFR 4.2).
"""
import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

OTP_PATHS = {"/api/auth/register", "/api/auth/login", "/api/auth/verify-otp", "/api/auth/resend-otp"}
MAX_ATTEMPTS = 3
WINDOW = 600
_store: dict = defaultdict(list)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in OTP_PATHS and request.method == "POST":
            ip = request.client.host if request.client else "unknown"
            key = f"otp:{ip}"
            now = time.time()
            _store[key] = [t for t in _store[key] if t > now - WINDOW]
            if len(_store[key]) >= MAX_ATTEMPTS:
                retry = int(WINDOW - (now - _store[key][0]))
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Too many OTP attempts. Retry in {retry}s."},
                    headers={"Retry-After": str(retry)},
                )
            _store[key].append(now)
        return await call_next(request)
