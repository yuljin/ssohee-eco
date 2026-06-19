from typing import Dict, List

from pydantic import BaseModel

from app.schemas.portfolio import PortfolioSnapshot


class TargetAllocation(BaseModel):
    weights: Dict[str, float]
    threshold: float = 0.10

    def validate_sum(self) -> None:
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Target weights must sum to 1.0, got {total}")


class TradeOrder(BaseModel):
    symbol: str
    side: str
    quantity: float
    value: float
    value_krw: float = 0.0


class RebalancePlan(BaseModel):
    orders: List[TradeOrder]


class RebalanceSimulationResult(BaseModel):
    before_snapshot: PortfolioSnapshot
    plan: RebalancePlan
    after_snapshot: PortfolioSnapshot
    exchange_rate: float = 0.0

