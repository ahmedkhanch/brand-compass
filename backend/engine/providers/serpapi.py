"""SerpAPI provider — Google SERP data for SEO scoring."""

import os
import requests

SERPAPI_URL = "https://serpapi.com/search"


class SerpAPIError(Exception):
    pass


class SerpAPIProvider:
    """Wraps SerpAPI for SEO data: organic results, knowledge panels, featured snippets."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise SerpAPIError("SERPAPI_KEY not set")

    def search(self, query: str, num: int = 10, **extra) -> dict:
        """Run a Google search via SerpAPI. Returns the full JSON response."""
        params = {
            "q": query,
            "api_key": self.api_key,
            "num": num,
            "hl": "en",
            "gl": "us",
            **extra,
        }
        resp = requests.get(SERPAPI_URL, params=params, timeout=30)
        if resp.status_code == 401:
            raise SerpAPIError("Invalid SERPAPI_KEY")
        if resp.status_code == 429:
            raise SerpAPIError("SerpAPI rate limit reached")
        resp.raise_for_status()
        return resp.json()

    def check_health(self) -> dict:
        """Quick check that the API key works."""
        data = self.search("test", num=1)
        return {
            "ok": True,
            "total_results": data.get("search_information", {}).get("total_results", 0),
        }
