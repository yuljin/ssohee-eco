from __future__ import annotations

from datetime import datetime


BLUE_CHIP_ASSETS = {"VOO", "QQQ", "SPY", "IVV", "TLT", "GLDM", "GLD", "AGG"}
LARGE_LOSS_THRESHOLD = -30.0


def should_enable_tax_loss_harvesting_for_symbol(
    symbol: str, pnl_pct: float, current_month: int | None = None
) -> bool:
    month = current_month or datetime.now().month
    if month == 12:
        return True
    if pnl_pct < LARGE_LOSS_THRESHOLD:
        return True
    if symbol.upper() in BLUE_CHIP_ASSETS:
        return False
    return False
