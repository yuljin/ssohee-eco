from __future__ import annotations

from collections import defaultdict
from typing import Dict, Tuple

from sqlalchemy.orm import Session

from app.core.config import KRW_SETTLED_SYMBOLS, settings
from app.models.transaction import Transaction
from app.schemas.portfolio import AssetPosition, PortfolioHoldings, PortfolioSnapshot


def compute_all_from_transactions(
    db: Session,
) -> Tuple[PortfolioHoldings, Dict[str, float], Dict[str, float]]:
    transactions = db.query(Transaction).order_by(Transaction.executed_at.asc(), Transaction.id.asc()).all()
    quantities: dict[str, float] = defaultdict(float)
    total_cost: dict[str, float] = defaultdict(float)
    total_qty: dict[str, float] = defaultdict(float)
    total_usd_cost: dict[str, float] = defaultdict(float)
    total_krw_cost: dict[str, float] = defaultdict(float)
    cash = settings.initial_cash

    for tx in transactions:
        side = tx.side.upper()
        symbol = tx.symbol.upper()
        if side not in {"BUY", "SELL", "DIVIDEND"}:
            continue

        amount = tx.quantity * tx.price
        fee = tx.fee or 0.0

        if side == "DIVIDEND":
            cash += amount
            continue

        if symbol == "CASH":
            cash += amount if side == "BUY" else -amount
            continue

        if side == "BUY":
            quantities[symbol] += tx.quantity
            if symbol not in KRW_SETTLED_SYMBOLS:
                cash -= amount + fee
            total_cost[symbol] += amount + fee
            total_qty[symbol] += tx.quantity
            if tx.exchange_rate:
                total_usd_cost[symbol] += amount + fee
                total_krw_cost[symbol] += (amount + fee) * tx.exchange_rate
        else:
            quantities[symbol] -= tx.quantity
            if symbol not in KRW_SETTLED_SYMBOLS:
                cash += amount - fee
            if total_qty[symbol] > 0:
                ratio = min(tx.quantity / total_qty[symbol], 1.0)
                total_cost[symbol] *= 1 - ratio
                total_qty[symbol] *= 1 - ratio
            if total_usd_cost[symbol] > 0:
                ratio = min(amount / total_usd_cost[symbol], 1.0)
                total_usd_cost[symbol] *= 1 - ratio
                total_krw_cost[symbol] *= 1 - ratio

    positions = {
        symbol: AssetPosition(symbol=symbol, quantity=quantity)
        for symbol, quantity in quantities.items()
        if quantity > 0.0001
    }
    avg_costs = {
        symbol: total_cost[symbol] / total_qty[symbol]
        for symbol in positions
        if total_qty[symbol] > 0.0001
    }
    avg_exchange_rates = {
        symbol: total_krw_cost[symbol] / total_usd_cost[symbol]
        for symbol in positions
        if total_usd_cost[symbol] > 0.0001
    }

    return PortfolioHoldings(positions=positions, cash=cash), avg_costs, avg_exchange_rates


def latest_exchange_rate_from_transactions(db: Session, fallback: float = 1400.0) -> float:
    tx = (
        db.query(Transaction)
        .filter(Transaction.exchange_rate.isnot(None))
        .order_by(Transaction.executed_at.desc(), Transaction.id.desc())
        .first()
    )
    return float(tx.exchange_rate) if tx and tx.exchange_rate else fallback


def latest_trade_prices_from_transactions(
    db: Session,
    symbols: list[str],
    avg_costs: Dict[str, float],
    manual_prices: Dict[str, float] | None = None,
) -> Dict[str, float]:
    manual_prices = manual_prices or {}
    prices: Dict[str, float] = {}
    for symbol in symbols:
        if symbol in manual_prices:
            prices[symbol] = manual_prices[symbol]
            continue
        tx = (
            db.query(Transaction)
            .filter(Transaction.symbol == symbol, Transaction.symbol != "CASH", Transaction.price > 0)
            .order_by(Transaction.executed_at.desc(), Transaction.id.desc())
            .first()
        )
        prices[symbol] = float(tx.price) if tx else avg_costs.get(symbol, 1.0)
    return prices


def evaluate_portfolio(
    holdings: PortfolioHoldings,
    prices: Dict[str, float],
    avg_costs: Dict[str, float] | None = None,
    exchange_rate: float = 0.0,
    avg_exchange_rates: Dict[str, float] | None = None,
) -> PortfolioSnapshot:
    avg_costs = avg_costs or {}
    avg_exchange_rates = avg_exchange_rates or {}
    value_by_symbol: dict[str, float] = {}
    quantity_by_symbol: dict[str, float] = {}
    pnl_pct_by_symbol: dict[str, float] = {}
    pnl_amount_by_symbol: dict[str, float] = {}
    pnl_pct_krw_by_symbol: dict[str, float] = {}
    pnl_amount_krw_by_symbol: dict[str, float] = {}

    for symbol, position in holdings.positions.items():
        price = prices.get(symbol)
        if price is None:
            raise KeyError(f"가격이 없습니다: {symbol}")
        value = position.quantity * price
        value_by_symbol[symbol] = value
        quantity_by_symbol[symbol] = position.quantity
        avg_cost = avg_costs.get(symbol, 0.0)
        if avg_cost > 0:
            cost_basis = avg_cost * position.quantity
            pnl_amount = value - cost_basis
            pnl_amount_by_symbol[symbol] = pnl_amount
            pnl_pct_by_symbol[symbol] = pnl_amount / cost_basis * 100
            avg_exchange = avg_exchange_rates.get(symbol, 0.0)
            if exchange_rate > 0 and avg_exchange > 0:
                krw_value = value * exchange_rate
                krw_cost = cost_basis * avg_exchange
                pnl_amount_krw_by_symbol[symbol] = krw_value - krw_cost
                pnl_pct_krw_by_symbol[symbol] = (krw_value - krw_cost) / krw_cost * 100

    value_by_symbol["CASH"] = holdings.cash
    quantity_by_symbol["CASH"] = holdings.cash
    pnl_pct_by_symbol["CASH"] = 0.0
    pnl_amount_by_symbol["CASH"] = 0.0
    pnl_pct_krw_by_symbol["CASH"] = 0.0
    pnl_amount_krw_by_symbol["CASH"] = 0.0
    avg_costs = {**avg_costs, "CASH": 1.0}

    total_value = sum(value_by_symbol.values())
    weight_by_symbol = {
        symbol: (value / total_value if total_value > 0 else 0.0)
        for symbol, value in value_by_symbol.items()
    }

    return PortfolioSnapshot(
        total_value=total_value,
        value_by_symbol=value_by_symbol,
        weight_by_symbol=weight_by_symbol,
        cash=holdings.cash,
        avg_cost_by_symbol=avg_costs,
        pnl_pct_by_symbol=pnl_pct_by_symbol,
        pnl_amount_by_symbol=pnl_amount_by_symbol,
        pnl_pct_krw_by_symbol=pnl_pct_krw_by_symbol,
        pnl_amount_krw_by_symbol=pnl_amount_krw_by_symbol,
        quantity_by_symbol=quantity_by_symbol,
        exchange_rate=exchange_rate,
        avg_exchange_rate_by_symbol=avg_exchange_rates,
    )
