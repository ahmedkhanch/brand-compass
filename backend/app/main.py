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
from app.database import init_db, close_db
from app.api.v1.router import router as v1_router
from app.api.v1.reports import sse_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables. Shutdown: close DB connection."""
    import logging
    logger = logging.getLogger("brand_compass")
    logger.info(f".env loaded: DEEPSEEK={'SET' if settings.DEEPSEEK_API_KEY else 'MISSING'}, "
                f"FIRECRAWL={'SET' if settings.FIRECRAWL_API_KEY else 'MISSING'}, "
                f"SERPAPI={'SET' if settings.SERPAPI_KEY else 'MISSING'}")
    logger.info("Creating database tables...")
    await init_db()
    logger.info("Startup complete — ready for requests")
    yield
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──
app.include_router(v1_router)
app.include_router(sse_router)  # SSE streaming endpoint


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
