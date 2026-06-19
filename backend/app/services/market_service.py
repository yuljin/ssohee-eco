from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Tuple

import yfinance as yf

from app.core.config import settings
from app.schemas.market import DrawdownAnalysis, DrawdownInfo
from app.services.price_service import TICKER_MAPPING, get_usd_krw_exchange_rate


def analyze_exchange_rate(period_days: int = 365) -> dict:
    current = get_usd_krw_exchange_rate() if settings.live_market_data else 1400.0
    if not settings.live_market_data:
        return {
            "current_rate": current,
            "period_days": period_days,
            "high": current,
            "low": current,
            "average": current,
            "from_high_pct": 0.0,
            "from_low_pct": 0.0,
            "from_avg_pct": 0.0,
            "signal": "평균 구간",
            "signal_color": "default",
            "recommendation": "실시간 시세 조회가 꺼져 있어 기본 환율로 표시합니다.",
            "history": [{"date": datetime.now().strftime("%Y-%m-%d"), "rate": current}],
        }
    end = datetime.now()
    start = end - timedelta(days=period_days)
    history: list[dict] = []
    try:
        df = yf.Ticker("KRW=X").history(start=start, end=end)
        history = [
            {"date": idx.strftime("%Y-%m-%d"), "rate": float(row["Close"])}
            for idx, row in df.dropna().iterrows()
            if row.get("Close", 0) > 0
        ]
    except Exception:
        history = []
    rates = [row["rate"] for row in history] or [current]
    high = max(rates)
    low = min(rates)
    average = sum(rates) / len(rates)
    from_high_pct = (current - high) / high * 100 if high else 0
    from_low_pct = (current - low) / low * 100 if low else 0
    from_avg_pct = (current - average) / average * 100 if average else 0
    if from_high_pct <= -7:
        signal, color, recommendation = "환전 적기", "success", "최근 고점 대비 충분히 낮은 환율입니다."
    elif from_high_pct <= -4:
        signal, color, recommendation = "환전 권장", "success", "분할 환전을 고려할 만한 구간입니다."
    elif from_avg_pct <= -2:
        signal, color, recommendation = "환전 고려", "warning", "평균보다 낮아 매수 자금 준비에 유리합니다."
    elif from_avg_pct <= 2:
        signal, color, recommendation = "평균 구간", "default", "무리 없는 정기 환전 구간입니다."
    elif from_avg_pct <= 5:
        signal, color, recommendation = "대기 권장", "warning", "평균보다 높아 분할 접근이 낫습니다."
    else:
        signal, color, recommendation = "환전 불리", "error", "환율 부담이 큰 구간입니다."
    return {
        "current_rate": current,
        "period_days": period_days,
        "high": high,
        "low": low,
        "average": average,
        "from_high_pct": from_high_pct,
        "from_low_pct": from_low_pct,
        "from_avg_pct": from_avg_pct,
        "signal": signal,
        "signal_color": color,
        "recommendation": recommendation,
        "history": history,
    }


def _period_high(symbol: str, weeks: int) -> Tuple[float, str, int]:
    if not settings.live_market_data:
        return 0.0, "", 0
    ticker = TICKER_MAPPING.get(symbol, symbol)
    end = datetime.now()
    start = end - timedelta(weeks=weeks)
    try:
        df = yf.Ticker(ticker).history(start=start, end=end)
        if df.empty:
            return 0.0, "", 0
        idx = df["High"].idxmax()
        high = float(df.loc[idx, "High"])
        days = (end.date() - idx.date()).days
        return high, idx.strftime("%Y-%m-%d"), days
    except Exception:
        return 0.0, "", 0


def _drawdown_signal(drawdown_pct: float) -> tuple[str, str]:
    if drawdown_pct > 50 or drawdown_pct < -95:
        return "error", "gray"
    if drawdown_pct >= -10:
        return "normal", "green"
    if drawdown_pct >= -20:
        return "consider", "yellow"
    return "buy", "red"


def analyze_drawdowns(symbols: Iterable[str], current_prices: Dict[str, float], weeks: int = 52) -> DrawdownAnalysis:
    rows: List[DrawdownInfo] = []
    for symbol in symbols:
        if symbol == "CASH" or symbol == "GOLD-KRX":
            continue
        current = current_prices.get(symbol, 0.0)
        high, high_date, days = _period_high(symbol, weeks)
        drawdown = (current - high) / high * 100 if high > 0 else 0.0
        signal, color = _drawdown_signal(drawdown)
        rows.append(
            DrawdownInfo(
                symbol=symbol,
                current_price=current,
                high_52w=high,
                high_52w_date=high_date,
                drawdown_pct=drawdown,
                signal=signal,
                signal_color=color,
                days_since_high=days,
            )
        )
    rows.sort(key=lambda item: item.drawdown_pct)
    return DrawdownAnalysis(
        symbols=rows,
        analysis_date=datetime.now().strftime("%Y-%m-%d"),
        total_symbols=len(rows),
        buy_signals=sum(1 for row in rows if row.signal == "buy"),
        consider_signals=sum(1 for row in rows if row.signal == "consider"),
    )


def cash_allocation_guide(analysis: DrawdownAnalysis, available_cash: float) -> Dict[str, float]:
    candidates = [row for row in analysis.symbols if row.signal in {"buy", "consider"}]
    total_weight = sum(abs(row.drawdown_pct) for row in candidates)
    if available_cash <= 0 or total_weight <= 0:
        return {}
    return {row.symbol: available_cash * abs(row.drawdown_pct) / total_weight for row in candidates}
