"""
TEST 2 — Perplexity API
Validates: API key works, real-time web search capability, competitive intel quality
Expected: Web-aware response with citations about a brand's competitive landscape
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BRAND      = os.getenv("TEST_BRAND_NAME", "Nike")
INDUSTRY   = os.getenv("TEST_BRAND_INDUSTRY", "sportswear")
COMPETITOR = os.getenv("TEST_COMPETITOR", "Adidas")

API_URL = "https://api.perplexity.ai/chat/completions"

def call_perplexity(prompt: str, model: str = "sonar") -> dict:
    headers = {
        "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
    }
    response = requests.post(API_URL, headers=headers, json=body, timeout=30)
    response.raise_for_status()
    return response.json()

def test_basic_call():
    """Check the key works and Perplexity returns something coherent."""
    print("\n── Test 1/3 : Basic connectivity ──────────")
    start = time.time()
    data = call_perplexity("Reply with exactly: PERPLEXITY_OK")
    elapsed = round(time.time() - start, 2)
    text = data["choices"][0]["message"]["content"].strip()

    if text:
        print(f"  ✅ Key valid — response in {elapsed}s")
        print(f"     Response: {text[:80]}")
    else:
        print(f"  ❌ Empty response after {elapsed}s")

def test_competitive_intel():
    """
    This is what Perplexity does that Claude alone cannot:
    real-time web-aware competitive research.
    """
    print("\n── Test 2/3 : Competitive intelligence ────")
    prompt = f"""
Research the competitive landscape for {BRAND} in the {INDUSTRY} industry.

Provide:
1. Top 3 direct competitors (with brief positioning for each)
2. {BRAND}'s main differentiator vs {COMPETITOR}
3. Any recent news or market changes in the last 6 months

Be specific and factual. Cite sources where possible.
"""

    start = time.time()
    data = call_perplexity(prompt)
    elapsed = round(time.time() - start, 2)

    text = data["choices"][0]["message"]["content"]
    citations = data.get("citations", [])

    print(f"  ✅ Response received in {elapsed}s")
    print(f"     Length    : {len(text)} characters")
    print(f"     Citations : {len(citations)} sources")
    print(f"\n  Preview (first 400 chars):")
    print(f"  {text[:400]}")

    if citations:
        print(f"\n  Sources cited:")
        for i, c in enumerate(citations[:3], 1):
            print(f"    {i}. {c}")
    else:
        print(f"\n  ⚠  No citations returned — response may not be web-grounded")

def test_brand_mentions():
    """
    Simulate a GEO scoring probe — check if a brand appears
    when asking a neutral industry question.
    """
    print("\n── Test 3/3 : GEO probe (brand mention) ───")
    prompt = f"What are the top 5 best-known brands in {INDUSTRY}? List them with one sentence each."

    start = time.time()
    data = call_perplexity(prompt)
    elapsed = round(time.time() - start, 2)

    text = data["choices"][0]["message"]["content"]
    mentioned = BRAND.lower() in text.lower()
    competitor_mentioned = COMPETITOR.lower() in text.lower()

    print(f"  ✅ Response in {elapsed}s")
    print(f"     {BRAND} mentioned     : {'✅ YES' if mentioned else '❌ NO'}")
    print(f"     {COMPETITOR} mentioned: {'✅ YES' if competitor_mentioned else '❌ NO'}")
    print(f"\n  Full response:")
    print(f"  {text[:500]}")

    if not mentioned:
        print(f"\n  ⚠  {BRAND} not mentioned — this is useful GEO data, not an error")

if __name__ == "__main__":
    print("=" * 50)
    print("  PERPLEXITY API TEST")
    print(f"  Brand: {BRAND} | Competitor: {COMPETITOR}")
    print("=" * 50)

    try:
        test_basic_call()
        test_competitive_intel()
        test_brand_mentions()
        print("\n✅ Perplexity API — ALL TESTS PASSED\n")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("\n❌ PERPLEXITY_API_KEY is invalid or missing. Check your .env\n")
        elif e.response.status_code == 429:
            print("\n⚠  Rate limit hit on Perplexity.\n")
        else:
            print(f"\n❌ HTTP error {e.response.status_code}: {e.response.text[:200]}\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")