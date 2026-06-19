from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import ASSET_GROUPS, DEFAULT_WEIGHTS
from app.services.market_service import analyze_drawdowns, analyze_exchange_rate
from app.services.portfolio_service import PortfolioSnapshot


def calculate_drawdown_score(drawdown_pct: float) -> float:
    if drawdown_pct > 50 or drawdown_pct < -95:
        return 0.0
    dd = abs(drawdown_pct)
    if dd <= 5:
        return dd * 2
    if dd <= 10:
        return 10 + (dd - 5) * 6
    if dd <= 20:
        return 40 + (dd - 10) * 4
    if dd <= 30:
        return 80 + (dd - 20) * 2
    return 100.0


def calculate_exchange_rate_score(from_avg_pct: float) -> float:
    x = from_avg_pct
    if x <= -7:
        return 100.0
    if x <= -4:
        return 70 + ((-4 - x) / 3) * 30
    if x <= -2:
        return 50 + ((-2 - x) / 2) * 20
    if x <= 0:
        return 30 + ((-x) / 2) * 20
    if x <= 2:
        return 30 - (x / 2) * 15
    if x <= 5:
        return 15 - ((x - 2) / 3) * 10
    return max(0.0, 5 - (x - 5))


def calculate_weight_score(target_weight: float, current_weight: float) -> float:
    if target_weight <= 0:
        return 0.0
    deviation = (target_weight - current_weight) / target_weight * 100
    if deviation <= 0:
        return 0.0
    if deviation <= 10:
        return deviation * 2
    if deviation <= 30:
        return 20 + (deviation - 10) * 2
    if deviation <= 50:
        return 60 + (deviation - 30) * 1.5
    return min(100.0, 90 + (deviation - 50) * 0.2)


def calculate_buy_ratio(score: float) -> float:
    if score <= 20:
        return 0.5
    if score <= 40:
        return 0.5 + (score - 20) / 20 * 0.3
    if score <= 60:
        return 0.8 + (score - 40) / 20 * 0.4
    if score <= 80:
        return 1.2 + (score - 60) / 20 * 0.4
    return 1.6 + (score - 80) / 20 * 0.4


def signal_info(score: float) -> tuple[str, str, str]:
    if score >= 70:
        return "적극 매수", "red", "하락폭과 비중 관점에서 적극 매수 구간입니다."
    if score >= 50:
        return "매수 권장", "orange", "기본 투입량 이상을 고려할 수 있습니다."
    if score >= 30:
        return "정상 투입", "blue", "정기 투입에 적합한 구간입니다."
    return "최소 투입", "green", "최소 투입량만 유지하는 구간입니다."


def generate_buy_timing_guide(
    db: Session,
    snapshot: PortfolioSnapshot,
    prices: dict[str, float],
    monthly_amount: float = 1000.0,
) -> dict:
    exchange = analyze_exchange_rate(365)
    exchange_score = calculate_exchange_rate_score(exchange["from_avg_pct"])
    target_weights = DEFAULT_WEIGHTS
    symbols = [s for s in target_weights if s != "CASH"]
    representative = [ASSET_GROUPS.get(s, [s])[0] for s in symbols]
    drawdowns = analyze_drawdowns(representative, prices, weeks=52)
    drawdown_by_symbol = {row.symbol: row.drawdown_pct for row in drawdowns.symbols}
    cash_weight = target_weights.get("CASH", 0.0)
    guides = []
    for symbol in symbols:
        members = ASSET_GROUPS.get(symbol, [symbol])
        current_weight = sum(snapshot.weight_by_symbol.get(member, 0.0) for member in members)
        target_weight = target_weights[symbol]
        drawdown_pct = drawdown_by_symbol.get(members[0], 0.0)
        drawdown_score = calculate_drawdown_score(drawdown_pct)
        weight_score = calculate_weight_score(target_weight, current_weight)
        total_score = drawdown_score * 0.4 + exchange_score * 0.3 + weight_score * 0.3
        buy_ratio = calculate_buy_ratio(total_score)
        effective_weight = target_weight / (1 - cash_weight) if cash_weight < 1 else target_weight
        base_amount = monthly_amount * effective_weight
        signal, color, desc = signal_info(total_score)
        guides.append(
            {
                "symbol": symbol,
                "current_price": prices.get(members[0], 0.0),
                "drawdown_pct": drawdown_pct,
                "drawdown_score": drawdown_score,
                "exchange_score": exchange_score,
                "weight_score": weight_score,
                "total_score": total_score,
                "buy_ratio": buy_ratio,
                "target_weight": target_weight * 100,
                "current_weight": current_weight * 100,
                "base_amount": base_amount,
                "recommended_amount": base_amount * buy_ratio,
                "signal": signal,
                "signal_color": color,
                "signal_desc": desc,
            }
        )
    guides.sort(key=lambda row: row["total_score"], reverse=True)
    average_score = sum(row["total_score"] for row in guides) / len(guides) if guides else 0
    reference_ratio = calculate_buy_ratio(average_score)
    actual_ratio = max(0.5, min(2.0, reference_ratio))
    return {
        "exchange_rate": exchange["current_rate"],
        "exchange_from_avg_pct": exchange["from_avg_pct"],
        "exchange_score": exchange_score,
        "monthly_amount": monthly_amount,
        "asset_guides": guides,
        "reference_ratio": reference_ratio,
        "reference_amount": monthly_amount * reference_ratio,
        "actual_ratio": actual_ratio,
        "actual_amount": monthly_amount * actual_ratio,
        "is_floor_applied": actual_ratio != reference_ratio and actual_ratio == 0.5,
        "message": "하락폭 40%, 환율 30%, 목표비중 부족분 30% 기준의 매수 타이밍입니다.",
        "warning": "환율이 평균보다 높습니다. 분할 환전을 고려하세요." if exchange["from_avg_pct"] > 5 else "",
    }

