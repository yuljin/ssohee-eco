from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    project_name: str = "ssohee-eco"
    api_v1_str: str = "/api/v1"
    database_url: str = f"sqlite:///{ROOT_DIR / 'data' / 'portfolio.db'}"
    initial_cash: float = 0.0
    live_market_data: bool = True
    app_basic_auth_user: Optional[str] = None
    app_basic_auth_password: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def sqlalchemy_database_url() -> str:
    url = settings.database_url
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgres://")
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url

KRW_SETTLED_SYMBOLS = {"GOLD-KRX", "BTC"}
MANUAL_PRICE_REQUIRED = {"GOLD-KRX"}
FRACTIONAL_ASSETS = {"BTC", "ETH"}

ASSET_GROUPS = {
    "GOLD": ["GLDM", "GOLD-KRX"],
}

DEFAULT_WEIGHTS = {
    "VOO": 0.40,
    "QQQ": 0.25,
    "TLT": 0.15,
    "GOLD": 0.10,
    "BTC": 0.05,
    "CASH": 0.05,
}

DEFAULT_THRESHOLD = 0.10
