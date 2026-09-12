"""FastAPI app factory — Brand Compass backend."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure backend/ is always on sys.path so both 'app' and 'engine'
# packages are importable regardless of the working directory.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# .env is loaded by app/config.py before Settings is instantiated,
# so both os.environ and settings.* have the API keys from the start.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import close_db
from app.core.private_responses import PrivateApiResponses
from app.api.v1.router import router as v1_router
from app.api.v1.reports import sse_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """The deployment runs Alembic before startup; the API never creates tables."""
    yield
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    redoc_url=None,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(PrivateApiResponses)

# ── Routes ──
app.include_router(v1_router)
app.include_router(sse_router)  # SSE streaming endpoint


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
