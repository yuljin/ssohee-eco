from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.portfolio import build_snapshot
from app.core.config import DEFAULT_WEIGHTS
from app.core.db import get_db
from app.schemas.market import DrawdownAnalysis
from app.services.buy_timing_service import generate_buy_timing_guide
from app.services.market_service import analyze_drawdowns, analyze_exchange_rate, cash_allocation_guide


drawdown_router = APIRouter(prefix="/api/v1/drawdown", tags=["drawdown"])
exchange_router = APIRouter(prefix="/api/v1/exchange-rate", tags=["exchange-rate"])
buy_timing_router = APIRouter(prefix="/api/v1/buy-timing", tags=["buy-timing"])


@drawdown_router.get("/analysis", response_model=DrawdownAnalysis)
def drawdown_analysis(weeks: int = Query(52), db: Session = Depends(get_db)):
    snapshot = build_snapshot(db)
    symbols = [symbol for symbol in snapshot.value_by_symbol if symbol != "CASH"] or ["VOO", "QQQ", "TLT", "GLDM", "BTC"]
    prices = {
        symbol: snapshot.value_by_symbol[symbol] / qty
        for symbol, qty in snapshot.quantity_by_symbol.items()
        if symbol != "CASH" and qty > 0
    }
    return analyze_drawdowns(symbols, prices, weeks)


@drawdown_router.get("/cash-guide")
def cash_guide(available_cash: float = Query(10000), weeks: int = Query(52), db: Session = Depends(get_db)):
    analysis = drawdown_analysis(weeks, db)
    return cash_allocation_guide(analysis, available_cash)


@exchange_router.get("/analysis")
def exchange_analysis(period_days: int = Query(365)):
    return analyze_exchange_rate(period_days)


@exchange_router.get("/guide")
def exchange_guide():
    return {
        label: analyze_exchange_rate(days)
        for label, days in {"3개월": 90, "6개월": 180, "1년": 365, "3년": 1095}.items()
    }


@buy_timing_router.get("/guide")
def buy_timing_guide(
    monthly_amount: float = Query(1000.0),
    gold_krx_price: Optional[float] = Query(None),
    db: Session = Depends(get_db),
):
    snapshot = build_snapshot(db, gold_krx_price)
    prices = {
        symbol: snapshot.value_by_symbol[symbol] / qty
        for symbol, qty in snapshot.quantity_by_symbol.items()
        if symbol != "CASH" and qty > 0
    }
    for symbol in DEFAULT_WEIGHTS:
        prices.setdefault(symbol, 0.0)
    return generate_buy_timing_guide(db, snapshot, prices, monthly_amount)
