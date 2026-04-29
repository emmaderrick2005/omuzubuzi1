"""
MOD-05: Payment processing service
- MTN MoMo + Airtel Money
- Escrow logic
- CRITICAL: NPS Act 2020 ID verification gate for txn >= UGX 1,000,000
"""
import uuid, httpx
from app.config import settings

KYC_THRESHOLD = settings.KYC_TRANSACTION_THRESHOLD  # 1,000,000 UGX

def requires_id_verification(amount: float) -> bool:
    """
    NPS Act 2020 compliance gate.
    Any transaction >= UGX 1,000,000 MUST have ID verification before proceeding.
    """
    return amount >= KYC_THRESHOLD

async def initiate_mtn_momo(phone: str, amount: float, order_id: str, currency: str = "UGX") -> dict:
    """
    Initiate MTN Mobile Money collection request.
    NOTE: Financial data (phone, amount) is NOT logged — NFR 4.2.
    """
    external_id = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {await _get_mtn_token()}",
        "X-Reference-Id": external_id,
        "X-Target-Environment": settings.MTN_MOMO_ENVIRONMENT,
        "Ocp-Apim-Subscription-Key": settings.MTN_MOMO_PRIMARY_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "amount": str(int(amount)),
        "currency": currency,
        "externalId": external_id,
        "payer": {"partyIdType": "MSISDN", "partyId": phone.lstrip("+")},
        "payerMessage": f"Omuzubuzi Order {order_id[:8]}",
        "payeeNote": "Omuzubuzi wholesale payment",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.MTN_MOMO_BASE_URL}/collection/v1_0/requesttopay",
            headers=headers,
            json=payload,
            timeout=30.0,
        )
    return {"reference_id": external_id, "status_code": resp.status_code, "accepted": resp.status_code == 202}

async def initiate_airtel_money(phone: str, amount: float, order_id: str) -> dict:
    """Initiate Airtel Money collection request."""
    token = await _get_airtel_token()
    payload = {
        "reference": f"OMZ-{order_id[:8]}",
        "subscriber": {"country": "UG", "currency": "UGX", "msisdn": phone.lstrip("+")},
        "transaction": {"amount": int(amount), "country": "UG", "currency": "UGX", "id": str(uuid.uuid4())},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.AIRTEL_BASE_URL}/merchant/v2/payments/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "X-Country": "UG", "X-Currency": "UGX"},
            json=payload,
            timeout=30.0,
        )
    data = resp.json()
    return {"reference_id": data.get("data", {}).get("transaction", {}).get("id"), "accepted": resp.status_code == 200}

async def _get_mtn_token() -> str:
    """Obtain MTN OAuth token."""
    import base64
    credentials = base64.b64encode(f"{settings.MTN_MOMO_API_USER}:{settings.MTN_MOMO_API_KEY}".encode()).decode()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.MTN_MOMO_BASE_URL}/collection/token/",
            headers={
                "Authorization": f"Basic {credentials}",
                "Ocp-Apim-Subscription-Key": settings.MTN_MOMO_PRIMARY_KEY,
            },
            timeout=10.0,
        )
    return resp.json().get("access_token", "")

async def _get_airtel_token() -> str:
    """Obtain Airtel OAuth2 token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.AIRTEL_BASE_URL}/auth/oauth2/token",
            json={"client_id": settings.AIRTEL_CLIENT_ID, "client_secret": settings.AIRTEL_CLIENT_SECRET, "grant_type": "client_credentials"},
            timeout=10.0,
        )
    return resp.json().get("access_token", "")
