"""Apify provider — Meta Ads Library scraper for competitive ad intelligence."""

import os
import requests

APIFY_BASE = "https://api.apify.com/v2"


class ApifyError(Exception):
    pass


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
        Uses dltik~facebook-ads-scraper (pay-per-result, no rental needed).
        """
        actor_id = "dltik~facebook-ads-scraper"
        run_url = f"{APIFY_BASE}/acts/{actor_id}/run-sync-get-dataset-items"

        params = {"token": self.token, "timeout": 180}
        body = {
            "searchTerms": brand_name,
            "country": country,
            "maxResults": max_results,
            "activeStatus": "active",
        }

        resp = requests.post(run_url, params=params, json=body, timeout=200)

        if resp.status_code == 401:
            raise ApifyError("Invalid APIFY_TOKEN")
        if resp.status_code == 403:
            raise ApifyError("Actor is not rented or not accessible with this plan")
        if resp.status_code == 402:
            raise ApifyError("Apify credits exhausted")
        if resp.status_code == 404:
            raise ApifyError(f"Actor '{actor_id}' not found — it may have been renamed or removed")
        resp.raise_for_status()

        data = resp.json()
        if isinstance(data, list):
            return data
        return []

    def check_health(self) -> dict:
        return self._check_health()
