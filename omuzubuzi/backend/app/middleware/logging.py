"""
Structured logging middleware.
CRITICAL (NFR 4.2): Financial data must NEVER appear in logs.
Scrubs payment amounts, account numbers, and provider references.
"""
import re
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Fields that must never be logged
SENSITIVE_FIELDS = {
    "amount", "total_amount", "price", "balance",
    "provider_ref", "transaction_id", "pin", "pin_hash",
    "national_id", "otp", "otp_hash", "card_number",
    "account_number", "access_token", "refresh_token",
}

FINANCIAL_ROUTES = {"/payments", "/payouts", "/receipts"}

log = structlog.get_logger()


def scrub_sensitive(data: dict) -> dict:
    """Recursively remove sensitive keys from log data."""
    if not isinstance(data, dict):
        return data
    return {
        k: "***REDACTED***" if k.lower() in SENSITIVE_FIELDS else scrub_sensitive(v)
        for k, v in data.items()
    }


class SecureLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Do not log body for financial endpoints
        is_financial = any(request.url.path.startswith(r) for r in FINANCIAL_ROUTES)

        log.info(
            "request_received",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
            financial_route=is_financial,
        )

        response = await call_next(request)

        log.info(
            "request_completed",
            path=request.url.path,
            status_code=response.status_code,
        )
        return response
