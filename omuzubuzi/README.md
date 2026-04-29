# Omuzubuzi — B2B Wholesale Marketplace

> "Delivering wholesale to your doorstep" | Kampala, Uganda

## Project Structure

```
omuzubuzi/
├── website/                  # Static marketing website (open index.html in browser)
│   └── index.html
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── main.py           # App entry point, middleware, router registration
│   │   ├── config.py         # Settings (env vars)
│   │   ├── database.py       # Async SQLAlchemy + PostgreSQL
│   │   ├── models.py         # Core ORM models (User, Wholesaler, Product, Order, Payment...)
│   │   ├── routers/          # API route handlers (auth, catalog, orders, payments...)
│   │   ├── services/         # Business logic (payments, notifications, delivery)
│   │   ├── middleware/        # Logging (financial data scrubbing), rate limiting
│   │   └── utils/            # Security (JWT/bcrypt), SMS (Africa's Talking)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example          # Copy to .env and fill in API keys
├── frontend/                 # React.js PWA
│   ├── src/
│   │   ├── pages/            # LoginPage, RegisterPage, MarketplacePage, etc.
│   │   ├── components/
│   │   ├── i18n/             # en.json + lg.json (Luganda translations)
│   │   ├── store/            # Redux state management
│   │   └── utils/api.js      # Axios API client
│   └── package.json
├── nginx/                    # Nginx reverse proxy config (TLS 1.2+)
├── scripts/                  # DB backup, retention enforcement scripts
├── .github/workflows/        # GitHub Actions CI/CD pipeline
└── docker-compose.yml        # Full stack orchestration

```

## Quick Start

### 1. Configure environment
```bash
cp backend/.env.example backend/.env
# Fill in: AT_API_KEY, MTN_MOMO_*, AIRTEL_*, AWS_*, SECRET_KEY
```

### 2. Run with Docker Compose
```bash
docker-compose up --build
```

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Website: open website/index.html in browser

## Key Regulatory Compliance

| Requirement | Implementation |
|---|---|
| NPS Act 2020 — ID check ≥ UGX 1M | `routers/payments.py` → `check_nps_id_verification()` |
| DPPA 2019 — no financial data in logs | `middleware/logging.py` → `scrub_sensitive()` |
| URA — 7-year transaction retention | `models.py` → `is_archived` flag + `scripts/retention.py` |
| Computer Misuse Act — audit trail | `models.py` → `AuditLog` table |
| bcrypt 12 rounds | `utils/security.py` → `CryptContext(bcrypt__rounds=12)` |
| TLS 1.2+ | `nginx/nginx.conf` → `ssl_protocols TLSv1.2 TLSv1.3` |

## Phase 1 MVP Modules

- ✅ MOD-01: Phone OTP auth (Africa's Talking), JWT, language toggle (EN/LG)
- ✅ MOD-03: Product catalog with MOQ and bulk price tiers
- ✅ MOD-05: MTN MoMo + Airtel Money + NPS Act ID gate
- ✅ MOD-02/04/06/07/08: Wholesaler, orders, delivery, notifications, admin (scaffolded)

## SRS Reference

Document ID: OMZ-SRS-001 v1.0 | Author: Emma — Lead Engineer | April 2026
