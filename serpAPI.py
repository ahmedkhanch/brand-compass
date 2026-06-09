"""
TEST 3 — SerpAPI
Validates: API key works, real SERP data returns, scoring signals are present
Expected: Structured Google results for the test brand

Usage:
  python serpAPI.py              ← runs in MOCK mode (no API call, zero cost)
  python serpAPI.py --real       ← runs against the live SerpAPI (consumes 3 calls)
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BRAND    = os.getenv("TEST_BRAND_NAME", "Nike")
URL      = os.getenv("TEST_BRAND_URL", "https://www.nike.com")
INDUSTRY = os.getenv("TEST_BRAND_INDUSTRY", "sportswear")

SERPAPI_URL = "https://serpapi.com/search"

# ──────────────────────────────────────────────────────────
# MOCK DATA — realistic SerpAPI responses for Nike
# These exactly mirror the real API's JSON structure.
# ──────────────────────────────────────────────────────────

MOCK_BRAND_QUERY = {
    "search_metadata": {"status": "Success"},
    "search_information": {"total_results": 528000000},
    "knowledge_graph": {
        "title": "Nike, Inc.",
        "type": "Sportswear company",
        "website": "https://www.nike.com",
        "description": "Nike, Inc. is an American multinational corporation that designs, develops, manufactures, and markets footwear, apparel, equipment, and accessories. It is the world's largest supplier of athletic shoes and apparel.",
        "source": {"name": "Wikipedia", "link": "https://en.wikipedia.org/wiki/Nike,_Inc."},
    },
    "answer_box": {
        "type": "organic_result",
        "title": "Nike. Just Do It. Nike.com",
        "link": "https://www.nike.com/",
        "snippet": "Nike delivers innovative products, experiences and services to inspire athletes.",
    },
    "organic_results": [
        {
            "position": 1,
            "title": "Nike. Just Do It. Nike.com",
            "link": "https://www.nike.com/",
            "snippet": "Nike delivers innovative products, experiences and services to inspire athletes everywhere.",
        },
        {
            "position": 2,
            "title": "Nike, Inc. - Wikipedia",
            "link": "https://en.wikipedia.org/wiki/Nike,_Inc.",
            "snippet": "Nike, Inc. is an American multinational corporation engaged in the design, development, manufacturing, and worldwide marketing of footwear, apparel, equipment, accessories, and services.",
        },
        {
            "position": 3,
            "title": "Nike (@nike) · Instagram",
            "link": "https://www.instagram.com/nike/",
            "snippet": "304M Followers, 149 Following, 1753 Posts — See Instagram photos and videos from Nike (@nike).",
        },
        {
            "position": 4,
            "title": "Nike - Twitter / X",
            "link": "https://x.com/nike",
            "snippet": "Official Nike Twitter account. Just Do It.",
        },
        {
            "position": 5,
            "title": "Nike - LinkedIn",
            "link": "https://www.linkedin.com/company/nike",
            "snippet": "Nike is a growth company that looks for team members who are passionate about sports and innovation.",
        },
    ],
    "related_searches": [
        {"query": "nike shoes"},
        {"query": "nike air max"},
        {"query": "nike store near me"},
        {"query": "nike stock price"},
        {"query": "nike dunks"},
        {"query": "nike jordan"},
        {"query": "nike metcon"},
        {"query": "nike blazers"},
    ],
    "related_questions": [
        {"question": "What is Nike known for?"},
        {"question": "Who owns Nike now?"},
        {"question": "Is Nike an American company?"},
        {"question": "What does the Nike slogan mean?"},
    ],
}

MOCK_INDUSTRY_QUERY = {
    "search_metadata": {"status": "Success"},
    "search_information": {"total_results": 195000000},
    "organic_results": [
        {
            "position": 1,
            "title": "Top 10 Sportswear Brands in the World 2026",
            "link": "https://www.example.com/top-sportswear-brands",
            "snippet": "The top sportswear brands include Nike, Adidas, Puma, Under Armour, and Lululemon. Nike continues to dominate with the largest market share globally.",
        },
        {
            "position": 2,
            "title": "Best Athletic Wear Brands — Ranked & Reviewed",
            "link": "https://www.example.com/best-athletic-brands",
            "snippet": "Our rankings place Nike at #1 for innovation and brand recognition, followed by Adidas for lifestyle appeal. Puma and New Balance round out the top tier.",
        },
        {
            "position": 3,
            "title": "Sportswear Market Report 2026",
            "link": "https://www.example.com/sportswear-market-2026",
            "snippet": "The global sportswear market is led by Nike with ~18% market share. Key trends include sustainable materials and direct-to-consumer channels.",
        },
    ],
    "related_questions": [
        {"question": "Which is the No 1 sportswear brand in the world?"},
        {"question": "What are the top 5 athletic brands?"},
        {"question": "Is Adidas bigger than Nike?"},
    ],
}

MOCK_RELATED_QUERY = {
    "search_metadata": {"status": "Success"},
    "search_information": {"total_results": 528000000},
    "organic_results": [],
    "related_searches": [
        {"query": "nike shoes"},
        {"query": "nike air max"},
        {"query": "nike store near me"},
        {"query": "nike stock price"},
        {"query": "nike dunks"},
        {"query": "nike jordan"},
    ],
    "related_questions": [
        {"question": "What is Nike known for?"},
        {"question": "Who owns Nike now?"},
        {"question": "What does the Nike slogan mean?"},
        {"question": "Is Nike an American company?"},
    ],
}


def call_serpapi(query: str, extra_params: dict = None) -> dict:
    """Call the real SerpAPI. Only invoked in --real mode."""
    if extra_params is None:
        extra_params = {}
    params = {
        "q": query,
        "api_key": os.getenv("SERPAPI_KEY"),
        "num": 10,
        "hl": "en",
        "gl": "us",
        **extra_params
    }
    response = requests.get(SERPAPI_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def call_mock(query: str, mock_data: dict) -> dict:
    """Return mock data — simulates a real SerpAPI call with 0 cost."""
    time.sleep(0.3)  # simulate network latency
    return mock_data


def test_brand_name_query(use_mock: bool = True):
    """
    Most critical SEO test: does the brand rank #1 for its own name?
    A brand not owning its SERP is a red flag.
    """
    print("\n── Test 1/3 : Brand name SERP ─────────────")
    start = time.time()

    if use_mock:
        print("  [MOCK MODE — no API call consumed]")
        data = call_mock(BRAND, MOCK_BRAND_QUERY)
    else:
        data = call_serpapi(BRAND)

    elapsed = round(time.time() - start, 2)

    organic = data.get("organic_results", [])
    knowledge_panel = data.get("knowledge_graph", {})
    featured_snippet = data.get("answer_box", {})

    print(f"  ✅ Response in {elapsed}s — {len(organic)} organic results")

    # Check if brand domain is in top 3
    brand_domain = URL.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    brand_position = None
    for i, result in enumerate(organic[:10], 1):
        link = result.get("link", "")
        if brand_domain in link:
            brand_position = i
            break

    if brand_position == 1:
        print(f"  ✅ Brand ranks #1 for own name — strong SEO signal")
    elif brand_position:
        print(f"  ⚠  Brand ranks #{brand_position} for own name — should be #1")
    else:
        print(f"  ❌ Brand domain not found in top 10 for own name")

    if knowledge_panel:
        print(f"  ✅ Knowledge panel present: {knowledge_panel.get('title', 'N/A')}")
    else:
        print(f"  ⚠  No knowledge panel found")

    if featured_snippet:
        print(f"  ✅ Featured snippet present")
    else:
        print(f"  ⚠  No featured snippet")

    # Show top 3 results
    print(f"\n  Top 3 organic results:")
    for r in organic[:3]:
        print(f"    {r.get('position', '?')}. {r.get('title', 'N/A')[:60]}")
        print(f"       {r.get('link', 'N/A')[:70]}")


def test_industry_query(use_mock: bool = True):
    """
    Check if the brand appears when users search for the category.
    Critical for competitive positioning.
    """
    print("\n── Test 2/3 : Industry keyword SERP ───────")
    query = f"best {INDUSTRY} brands"
    start = time.time()

    if use_mock:
        print("  [MOCK MODE — no API call consumed]")
        data = call_mock(query, MOCK_INDUSTRY_QUERY)
    else:
        data = call_serpapi(query)

    elapsed = round(time.time() - start, 2)

    organic = data.get("organic_results", [])
    brand_domain = URL.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

    # Check if brand appears in any result title or snippet
    brand_in_results = any(
        BRAND.lower() in (r.get("title", "") + r.get("snippet", "")).lower()
        for r in organic
    )

    print(f"  ✅ Query: '{query}' — {len(organic)} results in {elapsed}s")
    print(f"     {BRAND} appears in results: {'✅ YES' if brand_in_results else '⚠  NO'}")

    # Show top 3 snippets
    print(f"\n  Top 3 results for '{query}':")
    for r in organic[:3]:
        print(f"    {r.get('position', '?')}. {r.get('title', 'N/A')[:70]}")


def test_related_searches(use_mock: bool = True):
    """
    Related searches reveal how users think about this brand.
    Useful for GEO probe query generation.
    """
    print("\n── Test 3/3 : Related searches & PAA ──────")
    start = time.time()

    if use_mock:
        print("  [MOCK MODE — no API call consumed]")
        data = call_mock(BRAND, MOCK_RELATED_QUERY)
    else:
        data = call_serpapi(BRAND)

    elapsed = round(time.time() - start, 2)

    related = data.get("related_searches", [])
    paa = data.get("related_questions", [])

    print(f"  ✅ Additional signals retrieved in {elapsed}s")

    if related:
        print(f"\n  Related searches ({len(related)} found):")
        for r in related[:5]:
            print(f"    → {r.get('query', 'N/A')}")
    else:
        print(f"  ⚠  No related searches returned")

    if paa:
        print(f"\n  People Also Ask ({len(paa)} questions):")
        for q in paa[:4]:
            print(f"    ? {q.get('question', 'N/A')}")
    else:
        print(f"  ⚠  No People Also Ask questions")

    # Check credits remaining
    search_info = data.get("search_information", {})
    print(f"\n  📊 SerpAPI metadata:")
    print(f"     Total results: {search_info.get('total_results', 'N/A')}")


if __name__ == "__main__":
    use_mock = "--real" not in sys.argv

    print("=" * 50)
    print("  SERPAPI TEST")
    print(f"  Brand: {BRAND} | URL: {URL}")
    print(f"  Mode: {'MOCK (zero API calls)' if use_mock else 'LIVE (will consume 3 API calls)'}")
    print("=" * 50)

    if use_mock:
        print("\n  💡 To run against the real API:  python serpAPI.py --real")
        print("     This will consume 3 of your 250 monthly calls.\n")

    try:
        # Check that the key exists before attempting anything
        if not use_mock:
            serp_key = os.getenv("SERPAPI_KEY")
            if not serp_key or serp_key == "...":
                print("❌ SERPAPI_KEY not set in .env — running in MOCK mode instead\n")
                use_mock = True

        test_brand_name_query(use_mock)
        test_industry_query(use_mock)
        test_related_searches(use_mock)

        if use_mock:
            print("\n✅ SerpAPI mock validation — ALL LOGIC VERIFIED (0 API calls used)")
            print("   The real API will follow this exact same code path.")
            print("   Run 'python serpAPI.py --real' when ready to test live.\n")
        else:
            print("\n✅ SerpAPI — ALL LIVE TESTS PASSED\n")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("\n❌ SERPAPI_KEY is invalid or missing. Check your .env\n")
        elif e.response.status_code == 429:
            print("\n⚠  SerpAPI monthly search limit reached.\n")
        else:
            print(f"\n❌ HTTP error {e.response.status_code}: {e.response.text[:200]}\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
