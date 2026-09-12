"""Entitled access to collected ads; outbound collection stays behind this service."""
import asyncio
from datetime import datetime, timezone
from app.models import TierEnum
from app.repositories import reports
from app.services.entitlements import require_access
from app.services.report_access import owned_report


async def read_ads(db, report_id: str, user_id: str):
    report = await owned_report(db, report_id, user_id)
    await require_access(db, user_id, TierEnum.RADAR)
    payload = report.payload or {}
    if payload.get("meta_ads"):
        return {"report_id": report_id, "meta_ads": payload["meta_ads"]}
    from engine.providers.mock import provider_ready
    brand = payload.get("brand")
    unavailable = {"report_id": report_id, "meta_ads": None, "availability": "unavailable"}
    if not brand or not provider_ready("APIFY_TOKEN"):
        return unavailable
    from engine.providers.apify import ApifyProvider
    try:
        ads = await asyncio.to_thread(ApifyProvider().search_meta_ads, brand, max_results=20)
    except Exception:
        return unavailable
    result = {"total_ads_found": len(ads), "brand_name": brand, "ads": ads[:10],
              "source": "apify", "fetched_at": datetime.now(timezone.utc).isoformat()}
    await reports.save_ads(db, report, result)
    return {"report_id": report_id, "meta_ads": result, "availability": "available"}
