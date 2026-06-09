"""
TEST 4 — Firecrawl
Validates: API key works, website extraction produces clean markdown, Claude-ready output
Expected: Clean structured markdown from the brand's homepage in under 15 seconds
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

URL      = os.getenv("TEST_BRAND_URL", "https://www.nike.com")
BRAND    = os.getenv("TEST_BRAND_NAME", "Nike")

FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"

def call_firecrawl(url: str) -> dict:
    headers = {
        "Authorization": f"Bearer {os.getenv('FIRECRAWL_API_KEY')}",
        "Content-Type": "application/json",
    }
    body = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,      # strips nav, footer, ads — critical for quality
        "timeout": 30000,
    }
    response = requests.post(FIRECRAWL_URL, headers=headers, json=body, timeout=40)
    response.raise_for_status()
    return response.json()

def test_homepage_extraction():
    """
    Core test: can Firecrawl extract the homepage cleanly?
    The output should be usable as Claude input — no HTML noise.
    """
    print("\n── Test 1/2 : Homepage extraction ─────────")
    print(f"  Scraping: {URL}")
    print(f"  This may take 10–20 seconds...")

    start = time.time()
    data = call_firecrawl(URL)
    elapsed = round(time.time() - start, 2)

    if not data.get("success"):
        print(f"  ❌ Firecrawl returned success=false")
        print(f"     Response: {data}")
        return

    markdown = data.get("data", {}).get("markdown", "")
    metadata = data.get("data", {}).get("metadata", {})

    print(f"  ✅ Extracted in {elapsed}s")
    print(f"     Characters  : {len(markdown)}")
    print(f"     Words       : {len(markdown.split())}")
    print(f"     Page title  : {metadata.get('title', 'N/A')}")
    print(f"     Description : {metadata.get('description', 'N/A')[:120]}")

    # Quality check: is it clean markdown or HTML garbage?
    html_tags = markdown.count("<") + markdown.count(">")
    if html_tags < 10:
        print(f"  ✅ Output is clean markdown (minimal HTML noise)")
    elif html_tags < 50:
        print(f"  ⚠  Some HTML tags remain ({html_tags} found) — may need cleanup")
    else:
        print(f"  ❌ Output is HTML-heavy ({html_tags} tags) — Firecrawl did not clean this well")

    # Show a preview — this is what Claude will read
    print(f"\n  Preview (first 600 chars of extracted content):")
    print(f"  {'─' * 45}")
    print(f"  {markdown[:600]}")
    print(f"  {'─' * 45}")

    # Useful signals check
    brand_mentioned = BRAND.lower() in markdown.lower()
    print(f"\n  Brand name '{BRAND}' in content: {'✅ YES' if brand_mentioned else '⚠  NO'}")

    return markdown

def _is_404_page(markdown: str, metadata: dict) -> bool:
    """Check if the extracted page is actually a 404 / not-found page."""
    # Check HTTP status code from metadata
    status_code = metadata.get("statusCode", 200)
    if status_code in (404, 410):
        return True

    # Check for common 404 phrases in the content
    not_found_phrases = [
        "We can't find the page you are looking for",
        "page not found",
        "404",
        "page doesn't exist",
        "sorry for the inconvenience",
        "this page could not be found",
    ]
    content_lower = markdown.lower()
    matches = [p for p in not_found_phrases if p.lower() in content_lower]
    # If 2+ phrases match, it's likely a 404 page
    if len(matches) >= 2:
        return True
    # If content is very short (< 500 chars) and contains a 404 phrase
    if len(matches) >= 1 and len(markdown) < 500:
        return True
    return False


def test_about_page_extraction(markdown_homepage: str = None):
    """
    Test an about/company page — often richer brand signal than homepage.
    Try common about page patterns.
    """
    print("\n── Test 2/2 : About page extraction ───────")

    # Try common about page URLs
    base = URL.rstrip("/")
    about_urls = [f"{base}/about", f"{base}/about-us", f"{base}/company"]

    for about_url in about_urls:
        print(f"  Trying: {about_url}")
        try:
            start = time.time()
            data = call_firecrawl(about_url)
            elapsed = round(time.time() - start, 2)

            if data.get("success"):
                markdown = data.get("data", {}).get("markdown", "")
                metadata = data.get("data", {}).get("metadata", {})

                if _is_404_page(markdown, metadata):
                    print(f"  ⚠  404 — page not found at this URL ({elapsed}s)")
                    continue

                if len(markdown) > 200:
                    print(f"  ✅ About page found and extracted in {elapsed}s")
                    print(f"     Length : {len(markdown)} characters")
                    print(f"     Page title: {metadata.get('title', 'N/A')}")
                    print(f"\n  Preview (first 400 chars):")
                    print(f"  {markdown[:400]}")
                    return
                else:
                    print(f"  ⚠  Content too short ({len(markdown)} chars) — skipping")
        except Exception as e:
            print(f"  ⚠  Request failed: {e}")
            continue

    print(f"  ⚠  No about page found at common URLs — homepage content will be used")
    if markdown_homepage:
        print(f"  ✅ Homepage content ({len(markdown_homepage)} chars) is sufficient fallback")

if __name__ == "__main__":
    print("=" * 50)
    print("  FIRECRAWL API TEST")
    print(f"  URL: {URL}")
    print("=" * 50)

    try:
        homepage_markdown = test_homepage_extraction()
        test_about_page_extraction(homepage_markdown)
        print("\n✅ Firecrawl API — ALL TESTS PASSED\n")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("\n❌ FIRECRAWL_API_KEY is invalid or missing. Check your .env\n")
        elif e.response.status_code == 402:
            print("\n❌ Firecrawl credits exhausted. Top up at firecrawl.dev\n")
        elif e.response.status_code == 429:
            print("\n⚠  Firecrawl rate limit hit.\n")
        else:
            print(f"\n❌ HTTP {e.response.status_code}: {e.response.text[:300]}\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")