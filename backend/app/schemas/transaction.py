from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TransactionBase(BaseModel):
    side: str = Field(..., pattern="^(BUY|SELL|DIVIDEND)$")
    symbol: str
    quantity: float = Field(..., gt=0)
    price: float = Field(..., ge=0)
    fee: float = Field(0.0, ge=0)
    exchange_rate: Optional[float] = Field(None, gt=0)
    memo: Optional[str] = None

    @field_validator("side", "symbol")
    @classmethod
    def uppercase(cls, value: str) -> str:
        return value.strip().upper()


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int
    executed_at: datetime

    model_config = {"from_attributes": True}
