from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class PortfolioMetrics(BaseModel):
    total_deposit: float
    total_withdrawal: float
    net_invested: float
    current_value: float
    total_pnl: float
    total_return_pct: Optional[float] = None
    annualized_return_pct: Optional[float] = None
    total_deposit_krw: float
    total_withdrawal_krw: float
    net_invested_krw: float
    current_value_krw: float
    total_pnl_krw: float
    total_return_pct_krw: Optional[float] = None
    annualized_return_pct_krw: Optional[float] = None
    start_date: str
    end_date: str
    days_elapsed: int
    exchange_rate: float
    avg_deposit_exchange_rate: float


class MonthlyReturn(BaseModel):
    month: str
    start_value: float
    end_value: float
    net_deposit: float
    return_pct: float
    cumulative_return_pct: float
