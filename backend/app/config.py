"""Application configuration — all env vars with dev defaults."""

from pathlib import Path
from dotenv import load_dotenv

# Load .env BEFORE instantiating Settings, otherwise all API keys read as None.
# Find .env: go up from config.py (app/) → backend/ → project root
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── App ──
    APP_NAME: str = "Brand Compass"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ── Demo mode ──
    # When true, every paid provider (Firecrawl/SerpAPI/DeepSeek/Claude/OpenAI/
    # Perplexity/Apify) is replaced by brand-seeded mock fixtures so the full
    # pipeline runs with no API keys. See engine/providers/mock.py.
    DEMO_MODE: bool = False
    # Demo identity bypass must be opted into separately from mock providers.
    ALLOW_DEMO_AUTH: bool = False

    # ── Database ──
    # SQLite for local dev, PostgreSQL (asyncpg) for production.
    # Set DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/brandcompass for prod.
    DATABASE_URL: str = "sqlite+aiosqlite:///./brand_compass.db"

    # ── Redis (optional for local dev) ──
    REDIS_URL: Optional[str] = None

    # ── Clerk Auth ──
    CLERK_SECRET_KEY: Optional[str] = None
    CLERK_JWT_ISSUER: Optional[str] = None
    CLERK_JWT_AUDIENCE: Optional[str] = None
    CLERK_AUTHORIZED_PARTIES: str = ""

    # ── AI Providers ──
    ANTHROPIC_API_KEY: Optional[str] = None
    PERPLEXITY_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None

    # ── Data Providers ──
    SERPAPI_KEY: Optional[str] = None
    FIRECRAWL_API_KEY: Optional[str] = None
    APIFY_TOKEN: Optional[str] = None

    # ── Stripe ──
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_BOUSSOLE: Optional[str] = None
    STRIPE_PRICE_RADAR: Optional[str] = None
    STRIPE_PRICE_STRATEGE: Optional[str] = None

    # ── Email ──
    RESEND_API_KEY: Optional[str] = None

    # ── Tier Pricing (per product brief — authoritative) ──
    TIER_BOUSSOLE_PRICE: int = 99
    TIER_RADAR_PRICE: int = 199
    TIER_STRATEGE_PRICE: int = 499

    # ── Credit Limits (per tier) ──
    TIER_BOUSSOLE_CREDITS: int = 25
    TIER_RADAR_CREDITS: int = 100
    TIER_STRATEGE_CREDITS: int = 500

    # ── Rate Limits (req/min per tier) ──
    RATE_BOUSSOLE: int = 10
    RATE_RADAR: int = 30
    RATE_STRATEGE: int = 60

    # ── Cache ──
    BRAND_CACHE_TTL_HOURS: int = 24

    # .env is loaded at the top of this file (before Settings is instantiated).
    # Settings reads from os.environ, which now has all the keys.
    model_config = {"extra": "ignore"}


settings = Settings()
