from __future__ import annotations

from typing import Dict, List, Tuple

from app.core.config import ASSET_GROUPS, FRACTIONAL_ASSETS
from app.schemas.portfolio import PortfolioSnapshot
from app.schemas.rebalance import RebalancePlan, TargetAllocation, TradeOrder
from app.services.tax_loss_harvesting import should_enable_tax_loss_harvesting_for_symbol


def _expand_group_weights(
    allocation: TargetAllocation,
    snapshot: PortfolioSnapshot,
    prices: Dict[str, float],
    asset_groups: Dict[str, List[str]] | None = None,
) -> Dict[str, float]:
    groups = asset_groups or ASSET_GROUPS
    expanded: Dict[str, float] = {}
    for symbol, target_weight in allocation.weights.items():
        if symbol not in groups:
            expanded[symbol] = target_weight
            continue
        members = groups[symbol]
        member_values = {m: snapshot.value_by_symbol.get(m, 0.0) for m in members}
        total_value = sum(member_values.values())
        if total_value > 0:
            for member, value in member_values.items():
                expanded[member] = target_weight * (value / total_value)
        else:
            eligible = [m for m in members if m in prices]
            for member in eligible:
                expanded[member] = target_weight / len(eligible)
    return expanded


def generate_threshold_rebalance_plan(
    snapshot: PortfolioSnapshot,
    allocation: TargetAllocation,
    prices: Dict[str, float],
    exchange_rate: float = 0.0,
    enable_tax_loss_harvesting: bool | None = None,
    asset_groups: Dict[str, List[str]] | None = None,
) -> RebalancePlan:
    allocation.validate_sum()
    expanded_weights = _expand_group_weights(allocation, snapshot, prices, asset_groups)
    threshold = allocation.threshold
    total_value = snapshot.total_value
    to_sell: list[Tuple[str, float, float, float, float]] = []
    to_buy: list[Tuple[str, float, float, float]] = []

    for symbol, target_weight in expanded_weights.items():
        if symbol == "CASH" or symbol not in prices:
            continue
        current_value = snapshot.value_by_symbol.get(symbol, 0.0)
        current_weight = snapshot.weight_by_symbol.get(symbol, 0.0)
        target_value = target_weight * total_value
        diff_pct = round(current_weight - target_weight, 6)
        trade_value = target_value - current_value
        if diff_pct >= threshold:
            to_sell.append(
                (symbol, diff_pct, abs(trade_value), prices[symbol], snapshot.pnl_pct_by_symbol.get(symbol, 0.0))
            )
        elif current_value < target_value:
            to_buy.append((symbol, diff_pct, target_value - current_value, prices[symbol]))

    if not to_sell and not to_buy:
        return RebalancePlan(orders=[])

    if enable_tax_loss_harvesting is None:
        enable_tax_loss_harvesting = any(
            should_enable_tax_loss_harvesting_for_symbol(symbol, pnl_pct)
            for symbol, _, _, _, pnl_pct in to_sell
        )

    if enable_tax_loss_harvesting:
        to_sell.sort(key=lambda row: (row[4], -row[2]))
    else:
        to_sell.sort(key=lambda row: row[2], reverse=True)
    to_buy.sort(key=lambda row: row[2], reverse=True)

    orders: list[TradeOrder] = []
    available_cash = snapshot.value_by_symbol.get("CASH", 0.0)

    for symbol, _, sell_value, price, _ in to_sell:
        quantity = sell_value / price
        if symbol in FRACTIONAL_ASSETS:
            quantity = round(quantity, 6)
            if quantity < 0.000001:
                continue
        else:
            quantity = int(quantity)
            if quantity < 1:
                continue
        value = quantity * price
        available_cash += value
        orders.append(
            TradeOrder(
                symbol=symbol,
                side="SELL",
                quantity=quantity,
                value=value,
                value_krw=value * exchange_rate if exchange_rate > 0 else 0.0,
            )
        )

    target_cash = allocation.weights.get("CASH", 0.0) * total_value
    for symbol, _, buy_value, price in to_buy:
        usable_cash = available_cash - max(target_cash, 0.0)
        if usable_cash < 1.0:
            break
        if symbol in FRACTIONAL_ASSETS:
            value = min(buy_value, usable_cash)
            quantity = round(value / price, 6)
            if quantity < 0.000001:
                continue
        else:
            max_qty = int(usable_cash / price)
            target_qty = int(buy_value / price)
            quantity = min(max_qty, target_qty)
            if quantity < 1:
                continue
            value = quantity * price
        available_cash -= value
        orders.append(
            TradeOrder(
                symbol=symbol,
                side="BUY",
                quantity=quantity,
                value=value,
                value_krw=value * exchange_rate if exchange_rate > 0 else 0.0,
            )
        )

    return RebalancePlan(orders=orders)


def apply_rebalance_plan(snapshot: PortfolioSnapshot, plan: RebalancePlan) -> PortfolioSnapshot:
    values = dict(snapshot.value_by_symbol)
    quantities = dict(snapshot.quantity_by_symbol)
    cash = values.get("CASH", 0.0)
    for order in plan.orders:
        price = order.value / order.quantity if order.quantity else 0.0
        if order.side == "SELL":
            values[order.symbol] = max(0.0, values.get(order.symbol, 0.0) - order.value)
            quantities[order.symbol] = max(0.0, quantities.get(order.symbol, 0.0) - order.quantity)
            cash += order.value
        else:
            values[order.symbol] = values.get(order.symbol, 0.0) + order.value
            quantities[order.symbol] = quantities.get(order.symbol, 0.0) + order.quantity
            cash -= order.value
        if price <= 0:
            continue
    values["CASH"] = cash
    quantities["CASH"] = cash
    total = sum(values.values())
    weights = {symbol: value / total if total else 0.0 for symbol, value in values.items()}
    return snapshot.model_copy(update={"value_by_symbol": values, "quantity_by_symbol": quantities, "cash": cash, "total_value": total, "weight_by_symbol": weights})

