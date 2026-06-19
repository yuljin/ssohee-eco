from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Iterable, Optional

import requests
import yfinance as yf

from app.core.config import MANUAL_PRICE_REQUIRED


TICKER_MAPPING = {"BTC": "BTC-USD", "ETH": "ETH-USD"}
NASDAQ_SYMBOLS = {"VOO", "QQQ", "TLT", "GLDM"}
CACHE_SECONDS = 60
_executor = ThreadPoolExecutor(max_workers=6)
_price_cache: dict[str, tuple[float, float]] = {}
_exchange_rate_cache: tuple[float, float] | None = None


def _is_fresh(ts: float) -> bool:
    return time.time() - ts < CACHE_SECONDS


def _fetch_ticker_price(ticker: str) -> float:
    t = yf.Ticker(ticker)
    attempts = [
        lambda: getattr(t.fast_info, "last_price", None),
        lambda: t.info.get("regularMarketPrice"),
        lambda: t.history(period="5m", interval="1m")["Close"].dropna().iloc[-1],
        lambda: t.history(period="1d")["Close"].dropna().iloc[-1],
    ]
    for attempt in attempts:
        try:
            value = attempt()
            if value and float(value) > 0:
                return float(value)
        except Exception:
            continue
    raise ValueError(f"가격을 조회하지 못했습니다: {ticker}")


def _parse_money(value: str) -> float:
    return float(value.replace("$", "").replace(",", "").strip())


def _fetch_nasdaq_price(symbol: str) -> float:
    response = requests.get(
        f"https://api.nasdaq.com/api/quote/{symbol}/info",
        params={"assetclass": "etf"},
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.nasdaq.com",
            "Referer": "https://www.nasdaq.com/",
        },
        timeout=5,
    )
    response.raise_for_status()
    payload = response.json()
    value = payload["data"]["primaryData"]["lastSalePrice"]
    price = _parse_money(value)
    if price <= 0:
        raise ValueError(f"가격을 조회하지 못했습니다: {symbol}")
    return price


def _fetch_coinbase_spot(symbol: str) -> float:
    pair = {"BTC": "BTC-USD", "ETH": "ETH-USD"}[symbol]
    response = requests.get(f"https://api.coinbase.com/v2/prices/{pair}/spot", timeout=4)
    response.raise_for_status()
    price = float(response.json()["data"]["amount"])
    if price <= 0:
        raise ValueError(f"가격을 조회하지 못했습니다: {symbol}")
    return price


def get_usd_krw_exchange_rate() -> float:
    global _exchange_rate_cache
    if _exchange_rate_cache and _is_fresh(_exchange_rate_cache[1]):
        return _exchange_rate_cache[0]
    try:
        response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=4)
        response.raise_for_status()
        rate = float(response.json()["rates"]["KRW"])
    except Exception:
        try:
            rate = _fetch_ticker_price("KRW=X")
        except Exception:
            rate = 1400.0
    _exchange_rate_cache = (rate, time.time())
    return rate


def get_latest_prices(symbols: Iterable[str], manual_prices: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    manual_prices = manual_prices or {}
    result: Dict[str, float] = {}
    to_fetch: list[str] = []

    for raw_symbol in symbols:
        symbol = raw_symbol.upper()
        if symbol == "CASH":
            result[symbol] = 1.0
        elif symbol in manual_prices and manual_prices[symbol] and manual_prices[symbol] > 0:
            result[symbol] = float(manual_prices[symbol])
        elif symbol in _price_cache and _is_fresh(_price_cache[symbol][1]):
            result[symbol] = _price_cache[symbol][0]
        elif symbol not in MANUAL_PRICE_REQUIRED:
            to_fetch.append(symbol)

    futures = {}
    for symbol in to_fetch:
        if symbol in {"BTC", "ETH"}:
            futures[_executor.submit(_fetch_coinbase_spot, symbol)] = symbol
        elif symbol in NASDAQ_SYMBOLS:
            futures[_executor.submit(_fetch_nasdaq_price, symbol)] = symbol
        else:
            futures[_executor.submit(_fetch_ticker_price, TICKER_MAPPING.get(symbol, symbol))] = symbol

    for future in as_completed(futures):
        symbol = futures[future]
        try:
            price = future.result()
        except Exception:
            continue
        _price_cache[symbol] = (price, time.time())
        result[symbol] = price

    return result
