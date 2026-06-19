from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analytics import router as analytics_router
from app.api.market import buy_timing_router, drawdown_router, exchange_router
from app.api.portfolio import router as portfolio_router
from app.api.rebalance import router as rebalance_router
from app.api.transactions import router as transactions_router
from app.core.config import settings
from app.core.db import Base, engine
from app.models import Transaction  # noqa: F401


Base.metadata.create_all(bind=engine)

app = FastAPI(title="ssohee-eco API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolio_router)
app.include_router(rebalance_router)
app.include_router(transactions_router)
app.include_router(drawdown_router)
app.include_router(analytics_router)
app.include_router(exchange_router)
app.include_router(buy_timing_router)


@app.get("/health")
def health():
    return {"status": "ok", "project": settings.project_name}

