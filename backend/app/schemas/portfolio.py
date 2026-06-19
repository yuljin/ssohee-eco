from typing import Dict

from pydantic import BaseModel, Field


class AssetPosition(BaseModel):
    symbol: str
    quantity: float


class PortfolioHoldings(BaseModel):
    positions: Dict[str, AssetPosition]
    cash: float


class PortfolioSnapshot(BaseModel):
    total_value: float
    value_by_symbol: Dict[str, float]
    weight_by_symbol: Dict[str, float]
    cash: float
    avg_cost_by_symbol: Dict[str, float] = Field(default_factory=dict)
    pnl_pct_by_symbol: Dict[str, float] = Field(default_factory=dict)
    pnl_amount_by_symbol: Dict[str, float] = Field(default_factory=dict)
    pnl_pct_krw_by_symbol: Dict[str, float] = Field(default_factory=dict)
    pnl_amount_krw_by_symbol: Dict[str, float] = Field(default_factory=dict)
    quantity_by_symbol: Dict[str, float] = Field(default_factory=dict)
    exchange_rate: float = 0.0
    avg_exchange_rate_by_symbol: Dict[str, float] = Field(default_factory=dict)

