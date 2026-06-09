"""
TEST 5 — Apify (Meta Ads Library)
⚠ MOST CRITICAL TEST — run this before building anything else

Validates: Apify token works, Meta Ads scraper returns data for the target brand category
Expected: Active ads with copy, creative format and CTA type

If this fails for more than 2 out of 5 test brands → escalate to client immediately.
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BRAND = os.getenv("TEST_BRAND_NAME", "Nike")

APIFY_BASE = "https://api.apify.com/v2"

# Test brands across different sectors — run all 5 to detect category-specific blocks
TEST_BRANDS = [
    {"name": BRAND,        "sector": "your test brand"},
    {"name": "Apple",      "sector": "tech"},
    {"name": "Airbnb",     "sector": "travel / marketplace"},
    {"name": "Nespresso",  "sector": "FMCG / food & beverage"},
    {"name": "Adidas",     "sector": "sportswear / retail"},
]

def run_apify_actor(brand_name: str, country_code: str = "US") -> dict:
    """
    Triggers the Meta Ad Library scraper actor and waits for results.
    Uses the synchronous run endpoint for simplicity in testing.
    """
    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise ValueError("APIFY_TOKEN not set in .env")

    # Meta Ad Library scraper actor ID (pay-per-result, no rental needed)
    actor_id = "dltik~facebook-ads-scraper"

    run_url = f"{APIFY_BASE}/acts/{actor_id}/run-sync-get-dataset-items"

    params = {"token": token, "timeout": 120}
    body = {
        "searchTerms": brand_name,
        "country": country_code,
        "maxResults": 10,
        "activeStatus": "active",
    }

    response = requests.post(run_url, params=params, json=body, timeout=130)
    response.raise_for_status()
    return response.json()

def test_single_brand(brand: dict) -> bool:
    """Test Meta Ads access for one brand. Returns True if ads were found."""
    name    = brand["name"]
    sector  = brand["sector"]

    print(f"\n  Testing: {name} ({sector})")
    print(f"  Querying Meta Ads Library...")

    start = time.time()
    try:
        data = run_apify_actor(name)
        elapsed = round(time.time() - start, 2)

        if isinstance(data, list) and len(data) > 0:
            print(f"  ✅ {len(data)} ads found in {elapsed}s")

            # Show first ad details
            first_ad = data[0]
            page_name = first_ad.get("page_name", "N/A")
            body_text = first_ad.get("ad_text", "") or "No body text extracted"
            media_type = first_ad.get("media_type", "N/A")
            ctas = first_ad.get("detected_ctas", [])
            ctas_str = ", ".join(ctas) if ctas else "none"

            print(f"     Page name    : {page_name}")
            print(f"     Ad copy      : {str(body_text)[:120]}")
            print(f"     Media type   : {media_type}")
            print(f"     CTAs         : {ctas_str}")
            print(f"     Start date   : {first_ad.get('start_date', 'N/A')}")
            return True

        elif isinstance(data, list) and len(data) == 0:
            print(f"  ⚠  Actor ran but returned 0 ads in {elapsed}s")
            print(f"     This may mean: brand has no active ads, or access is restricted")
            return False
        else:
            print(f"  ⚠  Unexpected response format in {elapsed}s")
            print(f"     Type: {type(data)} | Preview: {str(data)[:200]}")
            return False

    except requests.exceptions.HTTPError as e:
        elapsed = round(time.time() - start, 2)
        if e.response.status_code == 404:
            print(f"  ❌ Actor not found — actor ID may have changed")
            print(f"     Go to apify.com and search for 'meta ads library scraper'")
        elif e.response.status_code == 402:
            print(f"  ❌ Apify credits exhausted")
        elif e.response.status_code == 401:
            print(f"  ❌ APIFY_TOKEN invalid")
        else:
            print(f"  ❌ HTTP {e.response.status_code}: {e.response.text[:200]}")
        return False

    except requests.exceptions.Timeout:
        print(f"  ❌ Request timed out after 130s — actor may be overloaded")
        return False

def test_token_validity():
    """Quick token check before running expensive actor tests."""
    print("\n── Test 1/2 : Token validity ───────────────")
    token = os.getenv("APIFY_TOKEN")
    if not token:
        print("  ❌ APIFY_TOKEN not set in .env")
        return False

    response = requests.get(
        f"{APIFY_BASE}/users/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )

    if response.status_code == 200:
        user = response.json().get("data", {})
        print(f"  ✅ Token valid")
        print(f"     Account  : {user.get('username', 'N/A')}")
        plan = user.get("plan", {})
        print(f"     Plan     : {plan.get('id', 'N/A')}")

        usage = user.get("limits", {})
        monthly_usd = usage.get("monthlyUsageCreditsUsd", "N/A")
        print(f"     Monthly budget: ${monthly_usd} USD")
        return True
    else:
        print(f"  ❌ Token invalid — HTTP {response.status_code}")
        return False

def test_meta_ads_multi_brand():
    """
    Run the scraper against 5 brands across different sectors.
    This is the real test — we need to know which sectors work.
    """
    print("\n── Test 2/2 : Meta Ads scraper (5 brands) ─")
    print("  Testing across sectors to detect category blocks...")
    print("  Each test may take 20–60 seconds.\n")

    results = {}
    for brand in TEST_BRANDS:
        success = test_single_brand(brand)
        results[brand["name"]] = {
            "sector": brand["sector"],
            "success": success
        }

    # Summary
    passed = sum(1 for r in results.values() if r["success"])
    total  = len(results)

    print(f"\n{'─' * 50}")
    print(f"  SUMMARY: {passed}/{total} brands returned ads")
    print(f"{'─' * 50}")

    for name, r in results.items():
        status = "✅" if r["success"] else "❌"
        print(f"  {status} {name} ({r['sector']})")

    print(f"\n  VERDICT:")
    if passed == total:
        print(f"  ✅ All brands returned ads — Meta Ads integration is SAFE to build")
    elif passed >= 3:
        print(f"  ⚠  Partial access — {total - passed} sector(s) blocked")
        print(f"     Build it, but document which sectors may have incomplete data")
    else:
        print(f"  ❌ CRITICAL: Only {passed}/{total} brands work")
        print(f"     DO NOT build the Meta Ads integration yet")
        print(f"     → Try a different Apify actor (search apify.com for alternatives)")
        print(f"     → Discuss fallback plan with client before proceeding")

if __name__ == "__main__":
    print("=" * 50)
    print("  APIFY — META ADS LIBRARY TEST")
    print(f"  ⚠ Most critical test in the project")
    print("=" * 50)

    try:
        token_ok = test_token_validity()
        if not token_ok:
            print("\n❌ Fix the token before running actor tests\n")
            exit(1)

        test_meta_ads_multi_brand()

    except ValueError as e:
        print(f"\n❌ Config error: {e}\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        raise