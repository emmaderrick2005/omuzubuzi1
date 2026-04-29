"""
Omuzubuzi B2B Wholesale Marketplace — FastAPI Backend
OMZ-SRS-001 v1.0 | Kampala, Uganda
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time, logging

from app.routers import auth, wholesalers, catalog, orders, payments, delivery, notifications, admin
from app.middleware.logging import SanitizedLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("omuzubuzi")

app = FastAPI(
    title="Omuzubuzi API",
    description="B2B Wholesale Marketplace Platform — Kampala, Uganda",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://omuzubuzi.ug", "https://app.omuzubuzi.ug", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SanitizedLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(round((time.time() - start) * 1000, 2))
    return response

app.include_router(auth.router,          prefix="/api/auth",          tags=["Authentication"])
app.include_router(wholesalers.router,   prefix="/api/wholesalers",   tags=["Wholesalers"])
app.include_router(catalog.router,       prefix="/api/products",      tags=["Catalog"])
app.include_router(orders.router,        prefix="/api/orders",        tags=["Orders"])
app.include_router(payments.router,      prefix="/api/payments",      tags=["Payments"])
app.include_router(delivery.router,      prefix="/api/deliveries",    tags=["Delivery"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(admin.router,         prefix="/api/admin",         tags=["Admin"])

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "platform": "Omuzubuzi", "version": "1.0.0"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {type(exc).__name__} on {request.url.path}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
