from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.core.db import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    side = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fee = Column(Float, nullable=False, default=0.0)
    exchange_rate = Column(Float, nullable=True)
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    memo = Column(String, nullable=True)

