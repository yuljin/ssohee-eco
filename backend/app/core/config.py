from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    project_name: str = "ssohee-eco"
    api_v1_str: str = "/api/v1"
    database_url: str = f"sqlite:///{ROOT_DIR / 'data' / 'portfolio.db'}"
    initial_cash: float = 0.0
    live_market_data: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

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
