"""
Rate limiter — in-memory fallback, Redis-ready interface.
Per tier: Boussole 10/min, Radar 30/min, Stratège 60/min.
"""

import time
from collections import defaultdict
from fastapi import HTTPException, Request
from app.config import settings
from app.models import TierEnum
from app.schemas.common import ERROR_RATE_LIMITED

TIER_RATE_MAP = {
    TierEnum.BOUSSOLE: settings.RATE_BOUSSOLE,
    TierEnum.RADAR: settings.RATE_RADAR,
    TierEnum.STRATEGE: settings.RATE_STRATEGE,
}

# In-memory store: {user_id: [(timestamp, ...), ...]}
_window: dict[str, list[float]] = defaultdict(list)


async def check_rate_limit(request: Request, user_id: str, tier: TierEnum = TierEnum.BOUSSOLE):
    """Check and update rate limit. Raises 429 if exceeded."""
    max_req = TIER_RATE_MAP.get(tier, settings.RATE_BOUSSOLE)
    now = time.time()
    window_start = now - 60  # 1-minute sliding window

    # Clean old entries
    _window[user_id] = [t for t in _window[user_id] if t > window_start]

    if len(_window[user_id]) >= max_req:
        retry_after = int(60 - (now - min(_window[user_id])))
        raise HTTPException(
            status_code=429,
            detail={"code": ERROR_RATE_LIMITED, "message": f"Rate limit reached. Retry in {retry_after}s"},
            headers={"Retry-After": str(retry_after)},
        )

    _window[user_id].append(now)
