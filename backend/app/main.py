import base64
import secrets
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

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


class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        username = settings.app_basic_auth_user
        password = settings.app_basic_auth_password
        if not username or not password:
            return await call_next(request)

        auth = request.headers.get("authorization", "")
        prefix = "Basic "
        valid = False
        if auth.startswith(prefix):
            try:
                decoded = base64.b64decode(auth.removeprefix(prefix)).decode("utf-8")
                supplied_user, supplied_password = decoded.split(":", 1)
                valid = secrets.compare_digest(supplied_user, username) and secrets.compare_digest(
                    supplied_password, password
                )
            except Exception:
                valid = False

        if valid:
            return await call_next(request)
        return Response(
            "Authentication required",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="ssohee-eco"'},
        )


app.add_middleware(BasicAuthMiddleware)

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


PUBLIC_DIR = Path(__file__).resolve().parents[3] / "public"
INDEX_HTML = PUBLIC_DIR / "index.html"
ASSETS_DIR = PUBLIC_DIR / "assets"

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


@app.get("/")
def serve_index():
    if INDEX_HTML.exists():
        return FileResponse(INDEX_HTML)
    return {"status": "frontend_not_built"}


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if INDEX_HTML.exists() and not full_path.startswith(("api/", "portfolio/", "rebalance/", "health")):
        return FileResponse(INDEX_HTML)
    return {"detail": "Not Found"}
