from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import ASSET_GROUPS, settings
from app.core.db import get_db
from app.schemas.market import PriceMap
from app.schemas.portfolio import PortfolioHoldings, PortfolioSnapshot
from app.services.portfolio_service import (
    compute_all_from_transactions,
    evaluate_portfolio,
    latest_exchange_rate_from_transactions,
    latest_trade_prices_from_transactions,
)
from app.services.price_service import get_latest_prices, get_usd_krw_exchange_rate


router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def build_snapshot(db: Session, gold_krx_price: Optional[float] = None) -> PortfolioSnapshot:
    holdings, avg_costs, avg_exchange_rates = compute_all_from_transactions(db)
    exchange_rate = get_usd_krw_exchange_rate() if settings.live_market_data else latest_exchange_rate_from_transactions(db)
    symbols = list(holdings.positions.keys())
    manual_prices = {}
    if gold_krx_price and exchange_rate > 0:
        manual_prices["GOLD-KRX"] = gold_krx_price / exchange_rate
    elif "GOLD-KRX" in holdings.positions:
        manual_prices["GOLD-KRX"] = avg_costs.get("GOLD-KRX", 0.0)
    if settings.live_market_data:
        try:
            prices = get_latest_prices(symbols, manual_prices=manual_prices)
        except Exception as exc:
            prices = {symbol: avg_costs.get(symbol, 1.0) for symbol in symbols}
            if not prices:
                raise HTTPException(status_code=502, detail=str(exc)) from exc
        fallback_prices = latest_trade_prices_from_transactions(db, symbols, avg_costs, manual_prices)
        prices = {**fallback_prices, **prices}
    else:
        prices = latest_trade_prices_from_transactions(db, symbols, avg_costs, manual_prices)
    return evaluate_portfolio(holdings, prices, avg_costs, exchange_rate, avg_exchange_rates)


@router.get("/holdings", response_model=PortfolioHoldings)
def holdings(db: Session = Depends(get_db)):
    return compute_all_from_transactions(db)[0]


@router.get("/snapshot", response_model=PortfolioSnapshot)
def snapshot(gold_krx_price: Optional[float] = Query(None), db: Session = Depends(get_db)):
    return build_snapshot(db, gold_krx_price)


@router.get("/status", response_model=PortfolioSnapshot)
def status(gold_krx_price: Optional[float] = Query(None), db: Session = Depends(get_db)):
    return build_snapshot(db, gold_krx_price)


@router.get("/prices", response_model=PriceMap)
def prices(db: Session = Depends(get_db)):
    holdings, avg_costs, _ = compute_all_from_transactions(db)
    symbols = list(holdings.positions.keys())
    if settings.live_market_data:
        try:
            result = get_latest_prices(symbols, manual_prices={"GOLD-KRX": avg_costs.get("GOLD-KRX", 0.0)})
        except Exception:
            result = {symbol: avg_costs.get(symbol, 1.0) for symbol in symbols}
    else:
        result = latest_trade_prices_from_transactions(db, symbols, avg_costs)
    return PriceMap(prices=result)


@router.get("/asset-groups")
def asset_groups():
    return ASSET_GROUPS
