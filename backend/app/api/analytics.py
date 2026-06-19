from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.portfolio import build_snapshot
from app.core.db import get_db
from app.schemas.analytics import MonthlyReturn, PortfolioMetrics
from app.services.analytics_service import calculate_metrics, monthly_returns


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/portfolio-metrics", response_model=PortfolioMetrics)
def portfolio_metrics(gold_krx_price: Optional[float] = Query(None), db: Session = Depends(get_db)):
    snapshot = build_snapshot(db, gold_krx_price)
    return calculate_metrics(db, snapshot)


@router.get("/monthly-returns", response_model=list[MonthlyReturn])
def monthly_return_list(gold_krx_price: Optional[float] = Query(None), db: Session = Depends(get_db)):
    snapshot = build_snapshot(db, gold_krx_price)
    return monthly_returns(db, snapshot)
