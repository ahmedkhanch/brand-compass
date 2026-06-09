"""Firecrawl provider — website content extraction for SEO keyword discovery."""

import os
import requests

FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"


class FirecrawlError(Exception):
    pass


class FirecrawlProvider:
    """Wraps Firecrawl for clean website markdown extraction."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise FirecrawlError("FIRECRAWL_API_KEY not set")

    def scrape(self, url: str, formats: list = None, timeout: int = 30000) -> dict:
        """Scrape a URL and return clean markdown + metadata."""
        if formats is None:
            formats = ["markdown"]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "url": url,
            "formats": formats,
            "onlyMainContent": True,
            "timeout": timeout,
        }
        resp = requests.post(FIRECRAWL_URL, headers=headers, json=body, timeout=40)

        if resp.status_code == 401:
            raise FirecrawlError("Invalid FIRECRAWL_API_KEY")
        if resp.status_code == 402:
            raise FirecrawlError("Firecrawl credits exhausted")
        resp.raise_for_status()

        data = resp.json()
        if not data.get("success"):
            raise FirecrawlError(f"Firecrawl returned success=false: {data}")
        return data

    def extract_text(self, url: str) -> tuple[str, dict]:
        """Scrape a URL and return (markdown_text, metadata)."""
        result = self.scrape(url)
        markdown = result.get("data", {}).get("markdown", "")
        metadata = result.get("data", {}).get("metadata", {})
        return markdown, metadata

    def check_health(self) -> dict:
        """Quick health check."""
        return {"ok": True}
