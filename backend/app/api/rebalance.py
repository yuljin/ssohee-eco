from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.portfolio import build_snapshot
from app.core.config import ASSET_GROUPS, DEFAULT_THRESHOLD, DEFAULT_WEIGHTS
from app.core.db import get_db
from app.schemas.rebalance import RebalanceSimulationResult, TargetAllocation
from app.services.price_service import get_latest_prices
from app.services.rebalance_service import apply_rebalance_plan, generate_threshold_rebalance_plan


router = APIRouter(prefix="/rebalance", tags=["rebalance"])
_current_allocation = TargetAllocation(weights=DEFAULT_WEIGHTS.copy(), threshold=DEFAULT_THRESHOLD)


@router.get("/config/allocation", response_model=TargetAllocation)
def get_allocation():
    return _current_allocation


@router.put("/config/allocation", response_model=TargetAllocation)
def update_allocation(payload: TargetAllocation):
    global _current_allocation
    try:
        payload.validate_sum()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _current_allocation = payload
    return _current_allocation


@router.get("/config/asset-groups")
def get_asset_groups():
    return ASSET_GROUPS


@router.get("/simulate", response_model=RebalanceSimulationResult)
def simulate(
    enable_tax_loss_harvesting: Optional[bool] = Query(None),
    gold_krx_price: Optional[float] = Query(None),
    db: Session = Depends(get_db),
):
    before = build_snapshot(db, gold_krx_price)
    prices = {
        symbol: before.value_by_symbol[symbol] / qty
        for symbol, qty in before.quantity_by_symbol.items()
        if symbol != "CASH" and qty > 0
    }
    for symbol in _current_allocation.weights:
        if symbol in {"CASH", "GOLD"} or symbol in prices:
            continue
        try:
            prices.update(get_latest_prices([symbol]))
        except Exception:
            pass
    plan = generate_threshold_rebalance_plan(
        before,
        _current_allocation,
        prices,
        exchange_rate=before.exchange_rate,
        enable_tax_loss_harvesting=enable_tax_loss_harvesting,
        asset_groups=ASSET_GROUPS,
    )
    after = apply_rebalance_plan(before, plan)
    return RebalanceSimulationResult(
        before_snapshot=before,
        plan=plan,
        after_snapshot=after,
        exchange_rate=before.exchange_rate,
    )
