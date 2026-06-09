"""
Brand-level cache with 24h TTL.
Per README §10: caches expensive provider responses per brand for 24 hours.
Cache key = SHA256(brand_name.lower() + website_url).

Uses the database (cached_results table) — no Redis dependency for local dev.
"""

import hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models import CachedResult


def make_cache_key(brand_name: str, website_url: str) -> str:
    """Generate a deterministic cache key for a brand."""
    raw = f"{brand_name.strip().lower()}|{website_url.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def get_cached(db: AsyncSession, brand_name: str, website_url: str, provider: str) -> dict | None:
    """
    Check the cache for a provider's result for this brand.
    Returns the cached payload or None.
    """
    cache_key = make_cache_key(brand_name, website_url)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(CachedResult).where(
            CachedResult.cache_key == cache_key,
            CachedResult.provider == provider,
            CachedResult.expires_at > now,
        )
    )
    cached = result.scalar_one_or_none()
    return cached.payload if cached else None


async def set_cache(db: AsyncSession, brand_name: str, website_url: str,
                    provider: str, payload: dict, ttl_hours: int = 24):
    """Store a provider result in the cache."""
    cache_key = make_cache_key(brand_name, website_url)
    now = datetime.now(timezone.utc)

    # Upsert: delete existing, insert new
    await db.execute(
        delete(CachedResult).where(
            CachedResult.cache_key == cache_key,
            CachedResult.provider == provider,
        )
    )

    cached = CachedResult(
        cache_key=cache_key,
        provider=provider,
        payload=payload,
        expires_at=now + timedelta(hours=ttl_hours),
    )
    db.add(cached)
    await db.flush()


async def invalidate_cache(db: AsyncSession, brand_name: str, website_url: str):
    """Remove all cached entries for a brand."""
    cache_key = make_cache_key(brand_name, website_url)
    await db.execute(delete(CachedResult).where(CachedResult.cache_key == cache_key))
    await db.flush()
