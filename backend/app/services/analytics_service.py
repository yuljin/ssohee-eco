from __future__ import annotations

from datetime import date
from typing import List

from sqlalchemy.orm import Session

from app.core.config import KRW_SETTLED_SYMBOLS
from app.models.transaction import Transaction
from app.schemas.analytics import MonthlyReturn, PortfolioMetrics
from app.schemas.portfolio import PortfolioSnapshot


def calculate_metrics(db: Session, snapshot: PortfolioSnapshot) -> PortfolioMetrics:
    transactions = db.query(Transaction).order_by(Transaction.executed_at.asc(), Transaction.id.asc()).all()
    if not transactions:
        return PortfolioMetrics(
            total_deposit=0,
            total_withdrawal=0,
            net_invested=0,
            current_value=snapshot.total_value,
            total_pnl=snapshot.total_value,
            total_deposit_krw=0,
            total_withdrawal_krw=0,
            net_invested_krw=0,
            current_value_krw=snapshot.total_value * snapshot.exchange_rate,
            total_pnl_krw=snapshot.total_value * snapshot.exchange_rate,
            start_date=date.today().isoformat(),
            end_date=date.today().isoformat(),
            days_elapsed=1,
            exchange_rate=snapshot.exchange_rate,
            avg_deposit_exchange_rate=0,
        )

    total_deposit = total_withdrawal = 0.0
    total_deposit_krw = total_withdrawal_krw = 0.0
    krw_asset_net_cost = krw_asset_net_cost_krw = 0.0
    deposit_usd_for_avg = deposit_krw_for_avg = 0.0

    for tx in transactions:
        amount = tx.quantity * tx.price
        fee = tx.fee or 0.0
        rate = tx.exchange_rate or snapshot.exchange_rate
        if tx.symbol.upper() == "CASH":
            if tx.side == "BUY":
                total_deposit += amount
                total_deposit_krw += amount * rate
                if tx.exchange_rate:
                    deposit_usd_for_avg += amount
                    deposit_krw_for_avg += amount * tx.exchange_rate
            elif tx.side == "SELL":
                total_withdrawal += amount
                total_withdrawal_krw += amount * rate
        elif tx.symbol.upper() in KRW_SETTLED_SYMBOLS:
            signed = 1 if tx.side == "BUY" else -1 if tx.side == "SELL" else 0
            net = amount + fee if tx.side == "BUY" else amount - fee
            krw_asset_net_cost += signed * net
            krw_asset_net_cost_krw += signed * net * rate

    net_invested = total_deposit - total_withdrawal + krw_asset_net_cost
    net_invested_krw = total_deposit_krw - total_withdrawal_krw + krw_asset_net_cost_krw
    total_pnl = snapshot.total_value - net_invested
    current_value_krw = snapshot.total_value * snapshot.exchange_rate
    total_pnl_krw = current_value_krw - net_invested_krw
    first = transactions[0].executed_at.date()
    days = max((date.today() - first).days, 1)
    years = days / 365.25
    total_return_pct = total_pnl / net_invested * 100 if net_invested > 0 else None
    total_return_pct_krw = total_pnl_krw / net_invested_krw * 100 if net_invested_krw > 0 else None
    annualized = ((snapshot.total_value / net_invested) ** (1 / years) - 1) * 100 if net_invested > 0 and years >= 1 else None
    annualized_krw = ((current_value_krw / net_invested_krw) ** (1 / years) - 1) * 100 if net_invested_krw > 0 and years >= 1 else None

    return PortfolioMetrics(
        total_deposit=total_deposit,
        total_withdrawal=total_withdrawal,
        net_invested=net_invested,
        current_value=snapshot.total_value,
        total_pnl=total_pnl,
        total_return_pct=total_return_pct,
        annualized_return_pct=annualized,
        total_deposit_krw=total_deposit_krw,
        total_withdrawal_krw=total_withdrawal_krw,
        net_invested_krw=net_invested_krw,
        current_value_krw=current_value_krw,
        total_pnl_krw=total_pnl_krw,
        total_return_pct_krw=total_return_pct_krw,
        annualized_return_pct_krw=annualized_krw,
        start_date=first.isoformat(),
        end_date=date.today().isoformat(),
        days_elapsed=days,
        exchange_rate=snapshot.exchange_rate,
        avg_deposit_exchange_rate=deposit_krw_for_avg / deposit_usd_for_avg if deposit_usd_for_avg > 0 else 0,
    )


def monthly_returns(db: Session, snapshot: PortfolioSnapshot) -> List[MonthlyReturn]:
    transactions = db.query(Transaction).order_by(Transaction.executed_at.asc(), Transaction.id.asc()).all()
    if not transactions:
        return []
    by_month: dict[str, float] = {}
    for tx in transactions:
        month = tx.executed_at.strftime("%Y-%m")
        amount = tx.quantity * tx.price
        if tx.symbol.upper() == "CASH":
            by_month[month] = by_month.get(month, 0.0) + (amount if tx.side == "BUY" else -amount)
        elif tx.symbol.upper() in KRW_SETTLED_SYMBOLS and tx.side in {"BUY", "SELL"}:
            by_month[month] = by_month.get(month, 0.0) + (amount if tx.side == "BUY" else -amount)

    months = sorted(by_month)
    if not months:
        return []
    running_deposit = 0.0
    cumulative = 1.0
    rows: list[MonthlyReturn] = []
    for month in months:
        start_value = running_deposit
        net_deposit = by_month[month]
        running_deposit += net_deposit
        is_last = month == months[-1]
        end_value = snapshot.total_value if is_last else running_deposit
        denom = start_value + net_deposit
        return_pct = ((end_value - start_value - net_deposit) / denom * 100) if denom > 0 else 0.0
        cumulative *= 1 + return_pct / 100
        rows.append(
            MonthlyReturn(
                month=month,
                start_value=start_value,
                end_value=end_value,
                net_deposit=net_deposit,
                return_pct=return_pct,
                cumulative_return_pct=(cumulative - 1) * 100,
            )
        )
    return rows

