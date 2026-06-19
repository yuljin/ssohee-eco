from typing import Dict, List

from pydantic import BaseModel


class DrawdownInfo(BaseModel):
    symbol: str
    current_price: float
    high_52w: float
    high_52w_date: str
    drawdown_pct: float
    signal: str
    signal_color: str
    days_since_high: int


class DrawdownAnalysis(BaseModel):
    symbols: List[DrawdownInfo]
    analysis_date: str
    total_symbols: int
    buy_signals: int
    consider_signals: int


class PriceMap(BaseModel):
    prices: Dict[str, float]

