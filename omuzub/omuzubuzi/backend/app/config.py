from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "CHANGE_ME"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379/0"

    AT_API_KEY: str = ""
    AT_USERNAME: str = "sandbox"
    AT_SENDER_ID: str = "OMUZUBUZI"

    MTN_MOMO_BASE_URL: str = "https://sandbox.momodeveloper.mtn.com"
    MTN_MOMO_COLLECTION_KEY: str = ""
    MTN_MOMO_COLLECTION_SECRET: str = ""
    MTN_MOMO_SUBSCRIPTION_KEY: str = ""

    AIRTEL_BASE_URL: str = "https://openapi.airtel.africa"
    AIRTEL_CLIENT_ID: str = ""
    AIRTEL_CLIENT_SECRET: str = ""

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "af-south-1"
    S3_BUCKET_NAME: str = "omuzubuzi-uploads"

    # NPS Act 2020 — identity verification threshold (UGX)
    NPS_ID_VERIFICATION_THRESHOLD: int = 1_000_000
    URA_TRANSACTION_RETENTION_YEARS: int = 7

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
