"""Apify provider — Meta Ads Library scraper for competitive ad intelligence."""

import os
import time
import requests

APIFY_BASE = "https://api.apify.com/v2"

ACTOR_ID = "dltik~facebook-ads-scraper"
POLL_INTERVAL_S = 3
MAX_POLL_S = 120


class ApifyError(Exception):
    pass


def _normalize_ad(raw: dict) -> dict:
    """Map a raw Meta Ads Library item to the shape the report UI consumes.

    Keeps only what the Meta Ads section renders: brand, format, copy, a
    visual, and the Ad Library snapshot URL (clickable to the real ad).
    """
    images = raw.get("images") or []
    image_url = images[0] if images else (raw.get("page_profile_pic") or None)
    return {
        "page_name": raw.get("page_name") or "",
        "media_type": raw.get("media_type") or "",
        "ad_text": raw.get("ad_text") or raw.get("title") or "",
        "image_url": image_url,
        "snapshot_url": raw.get("ad_snapshot_url") or None,
        "cta_text": raw.get("cta_text") or None,
        "start_date": raw.get("start_date") or None,
        "is_active": raw.get("is_active"),
    }


class ApifyProvider:
    """Wraps Apify Meta Ads scraper for competitive ad data."""

    def __init__(self, api_key: str = None):
        self.token = api_key or os.getenv("APIFY_TOKEN")
        if not self.token:
            raise ApifyError("APIFY_TOKEN not set")

    def _check_health(self) -> dict:
        """Verify the token is valid."""
        resp = requests.get(
            f"{APIFY_BASE}/users/me",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            user = resp.json().get("data", {})
            return {"ok": True, "username": user.get("username")}
        raise ApifyError(f"Invalid APIFY_TOKEN (HTTP {resp.status_code})")

    def search_meta_ads(self, brand_name: str, country: str = "US", max_results: int = 50) -> list:
        """
        Run the Meta Ads Library scraper and return ad results.

        Free-plan accounts cannot use the synchronous run endpoint, so we use
        the two-step async path: create a run → poll until SUCCEEDED → fetch
        dataset items.
        """
        # ── 1. Create run ───────────────────────────────────────────
        create_url = f"{APIFY_BASE}/acts/{ACTOR_ID}/runs"
        body = {
            "searchTerms": brand_name,
            "country": country,
            "maxResults": max_results,
            "activeStatus": "active",
        }

        resp = requests.post(create_url, params={"token": self.token}, json=body, timeout=30)

        if resp.status_code == 401:
            raise ApifyError("Invalid APIFY_TOKEN")
        if resp.status_code == 403:
            raise ApifyError("Actor is not rented or not accessible with this plan")
        if resp.status_code == 402:
            raise ApifyError("Apify credits exhausted")
        if resp.status_code == 404:
            raise ApifyError(f"Actor '{ACTOR_ID}' not found — it may have been renamed or removed")
        resp.raise_for_status()

        run_data = resp.json().get("data", {})
        run_id = run_data.get("id")
        if not run_id:
            raise ApifyError("Apify run created but no run ID returned")

        # ── 2. Poll for completion ──────────────────────────────────
        status_url = f"{APIFY_BASE}/actor-runs/{run_id}"
        elapsed = 0
        status = run_data.get("status", "READY")
        while elapsed < MAX_POLL_S:
            if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                break
            time.sleep(POLL_INTERVAL_S)
            elapsed += POLL_INTERVAL_S
            poll_resp = requests.get(status_url, params={"token": self.token}, timeout=10)
            poll_resp.raise_for_status()
            status = poll_resp.json().get("data", {}).get("status", "?")

        if status != "SUCCEEDED":
            raise ApifyError(f"Apify run {run_id} ended with status={status} after {elapsed}s")

        # ── 3. Fetch dataset items ──────────────────────────────────
        dataset_id = poll_resp.json().get("data", {}).get("defaultDatasetId", "")
        if not dataset_id:
            raise ApifyError(f"Apify run {run_id} succeeded but no datasetId returned")

        dataset_url = f"{APIFY_BASE}/datasets/{dataset_id}/items"
        ds_resp = requests.get(dataset_url, params={"token": self.token, "limit": max_results}, timeout=30)
        ds_resp.raise_for_status()

        data = ds_resp.json()
        if isinstance(data, list):
            return [_normalize_ad(a) for a in data if isinstance(a, dict)]
        return []

    def check_health(self) -> dict:
        return self._check_health()
