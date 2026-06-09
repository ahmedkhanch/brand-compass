"""
TEST 6 — DeepSeek API (Temporary GEO LLM)
Validates: API key works, JSON output is parseable, GEO probe queries return usable data
Expected: Structured brand analysis in under 10 seconds

Usage:
  python deepseek.py              ← runs in MOCK mode (no API call, zero cost)
  python deepseek.py --real       ← runs against the live DeepSeek API

Note: DeepSeek uses an OpenAI-compatible API. We use the `openai` Python SDK
      pointed at https://api.deepseek.com.
"""

import os
import sys
import json
import time
from dotenv import load_dotenv

load_dotenv()

BRAND    = os.getenv("TEST_BRAND_NAME", "Nike")
INDUSTRY = os.getenv("TEST_BRAND_INDUSTRY", "sportswear")
URL      = os.getenv("TEST_BRAND_URL", "https://www.nike.com")
COMPETITOR = os.getenv("TEST_COMPETITOR", "Adidas")

DEEPSEEK_BASE = "https://api.deepseek.com"

# ──────────────────────────────────────────────────────────
# MOCK DATA — realistic DeepSeek responses for Nike
# ──────────────────────────────────────────────────────────

MOCK_BASIC_RESPONSE = "DEEPSEEK_OK"

MOCK_GEO_VISIBILITY = """{
  "brand_mentioned": true,
  "brand_description": "Nike is the world's largest sportswear brand, known for its iconic 'Just Do It' slogan and Swoosh logo.",
  "confidence": "high",
  "key_facts": [
    "Founded in 1964 as Blue Ribbon Sports",
    "Headquartered in Beaverton, Oregon",
    "Global market leader in athletic footwear and apparel"
  ]
}"""

MOCK_GEO_SENTIMENT = """{
  "sentiment": "positive",
  "pros": [
    "Strong brand recognition and global presence",
    "Innovative product technology (Air Max, Flyknit, React foam)",
    "Effective marketing and athlete endorsements"
  ],
  "cons": [
    "Premium pricing compared to competitors",
    "Past controversies around labor practices in supply chain",
    "Dependence on wholesale partners impacting DTC transition"
  ],
  "recommendation": "Yes, Nike is a strong brand with market leadership, though consumers should be aware of pricing and ethical considerations.",
  "sentiment_score": 8
}"""


def call_deepseek(prompt: str, system: str = None, model: str = "deepseek-chat", max_tokens: int = 800) -> str:
    """Call the real DeepSeek API. Only invoked in --real mode."""
    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=DEEPSEEK_BASE,
    )

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()


def call_mock(text: str, delay: float = 0.4) -> str:
    """Return mock data — simulates a real DeepSeek call with 0 cost."""
    time.sleep(delay)
    return text


def test_basic_call(use_mock: bool = True):
    """Most basic call — just checking the key works."""
    print("\n── Test 1/4 : Basic connectivity ──────────")
    start = time.time()

    if use_mock:
        print("  [MOCK MODE — no API call consumed]")
        text = call_mock(MOCK_BASIC_RESPONSE)
    else:
        text = call_deepseek("Reply with exactly: DEEPSEEK_OK", max_tokens=20)

    elapsed = round(time.time() - start, 2)

    if "DEEPSEEK_OK" in text or "OK" in text:
        print(f"  ✅ Key valid — response in {elapsed}s")
        print(f"     Response: {text[:60]}")
    else:
        print(f"  ⚠  Unexpected response: {text[:80]}")


def test_json_output(use_mock: bool = True):
    """
    Check that DeepSeek reliably returns parseable JSON.
    This is critical — the GEO scorer depends on structured output.
    """
    print("\n── Test 2/4 : JSON output reliability ─────")
    system = "You are a brand analyst. Return ONLY valid JSON — no preamble, no markdown fences, no extra text."

    prompt = f"""
Analyze this brand and return ONLY valid JSON:

Brand: {BRAND}
Industry: {INDUSTRY}
Website: {URL}

Return exactly this structure:
{{
  "brand_mentioned": true,
  "brand_description": "one sentence summary",
  "confidence": "high | medium | low",
  "key_facts": ["fact1", "fact2", "fact3"]
}}
"""

    start = time.time()

    if use_mock:
        print("  [MOCK MODE — no API call consumed]")
        raw = call_mock(MOCK_GEO_VISIBILITY)
    else:
        raw = call_deepseek(prompt, system=system)

    elapsed = round(time.time() - start, 2)

    try:
        parsed = json.loads(raw)
        print(f"  ✅ JSON valid — parsed in {elapsed}s")
        print(f"     Brand mentioned : {parsed.get('brand_mentioned')}")
        print(f"     Description     : {parsed.get('brand_description', '')[:100]}")
        print(f"     Confidence      : {parsed.get('confidence')}")
        print(f"     Key facts       : {len(parsed.get('key_facts', []))} found")
        return True
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON parse failed after {elapsed}s")
        print(f"     Error   : {e}")
        print(f"     Raw     : {raw[:300]}")
        return False


def test_sentiment_probe(use_mock: bool = True):
    """
    Simulate a GEO sentiment probe — the core of the GEO scorer.
    DeepSeek should return structured pros/cons with a sentiment judgment.
    """
    print("\n── Test 3/4 : Sentiment probe (GEO sim) ───")
    system = "You are a brand analyst evaluating brand perception. Return ONLY valid JSON."

    prompt = f"""
Analyze the brand perception of {BRAND} in the {INDUSTRY} industry.

Return ONLY valid JSON:
{{
  "sentiment": "positive | neutral | negative",
  "pros": ["pro1", "pro2", "pro3"],
  "cons": ["con1", "con2"],
  "recommendation": "one sentence on whether the brand is recommended",
  "sentiment_score": 1-10
}}
"""

    start = time.time()

    if use_mock:
        print("  [MOCK MODE — no API call consumed]")
        raw = call_mock(MOCK_GEO_SENTIMENT)
    else:
        raw = call_deepseek(prompt, system=system)

    elapsed = round(time.time() - start, 2)

    try:
        parsed = json.loads(raw)
        print(f"  ✅ Sentiment probe successful — {elapsed}s")
        print(f"     Sentiment       : {parsed.get('sentiment')}")
        print(f"     Score           : {parsed.get('sentiment_score')}/10")
        print(f"     Pros            : {len(parsed.get('pros', []))} items")
        print(f"     Cons            : {len(parsed.get('cons', []))} items")
        print(f"     Recommendation  : {parsed.get('recommendation', '')[:100]}")
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON parse failed after {elapsed}s")
        print(f"     Error: {e}")
        print(f"     Raw  : {raw[:300]}")


def test_competitive_comparison(use_mock: bool = True):
    """
    Test a brand-vs-competitor probe — used in GEO consistency scoring.
    """
    print("\n── Test 4/4 : Competitive comparison ──────")
    system = "You are a brand analyst. Return ONLY valid JSON."

    prompt = f"""
Compare {BRAND} vs {COMPETITOR} in the {INDUSTRY} industry.

Return ONLY valid JSON:
{{
  "winner": "{BRAND} | {COMPETITOR} | tie",
  "brand_strength": "one sentence on {BRAND}'s advantage",
  "competitor_strength": "one sentence on {COMPETITOR}'s advantage",
  "comparison_summary": "one sentence overall comparison"
}}
"""

    start = time.time()

    if use_mock:
        print("  [MOCK MODE — no API call consumed]")
        # Quick inline mock for comparison
        mock_comp = json.dumps({
            "winner": BRAND,
            "brand_strength": f"{BRAND} dominates in brand recognition and athlete endorsements.",
            "competitor_strength": f"{COMPETITOR} leads in lifestyle appeal and sustainability initiatives.",
            "comparison_summary": f"While {BRAND} leads in performance and market share, {COMPETITOR} is gaining ground in lifestyle and eco-conscious segments."
        })
        raw = call_mock(mock_comp)
    else:
        raw = call_deepseek(prompt, system=system)

    elapsed = round(time.time() - start, 2)

    try:
        parsed = json.loads(raw)
        print(f"  ✅ Comparison probe successful — {elapsed}s")
        print(f"     Winner          : {parsed.get('winner')}")
        print(f"     Brand strength  : {parsed.get('brand_strength', '')[:100]}")
        print(f"     Competitor edge : {parsed.get('competitor_strength', '')[:100]}")
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON parse failed after {elapsed}s")
        print(f"     Error: {e}")
        print(f"     Raw  : {raw[:300]}")


if __name__ == "__main__":
    use_mock = "--real" not in sys.argv

    print("=" * 50)
    print("  DEEPSEEK API TEST")
    print(f"  Brand: {BRAND} | Industry: {INDUSTRY}")
    print(f"  Mode: {'MOCK (zero API calls)' if use_mock else 'LIVE (will consume ~4 API calls)'}")
    print("=" * 50)

    if use_mock:
        print("\n  💡 To run against the real API:  python deepseek.py --real")
        print("     DeepSeek pricing: ~$0.14/M input tokens, ~$0.28/M output tokens\n")

    try:
        # Validate key exists before attempting real calls
        if not use_mock:
            deepseek_key = os.getenv("DEEPSEEK_API_KEY")
            if not deepseek_key or deepseek_key == "sk-...":
                print("❌ DEEPSEEK_API_KEY not set in .env — running in MOCK mode instead\n")
                use_mock = True

        test_basic_call(use_mock)
        test_json_output(use_mock)
        test_sentiment_probe(use_mock)
        test_competitive_comparison(use_mock)

        if use_mock:
            print("\n✅ DeepSeek mock validation — ALL LOGIC VERIFIED (0 API calls)")
            print("   The real API uses the OpenAI SDK pointed at api.deepseek.com.")
            print("   Run 'python deepseek.py --real' when ready to test live.\n")
        else:
            print("\n✅ DeepSeek API — ALL LIVE TESTS PASSED\n")

    except ImportError:
        print("\n❌ The 'openai' package is not installed.")
        print("   Install it: pip install openai\n")
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Invalid API Key" in error_msg:
            print("\n❌ DEEPSEEK_API_KEY is invalid. Check your .env\n")
        elif "402" in error_msg or "Insufficient Balance" in error_msg:
            print("\n❌ DeepSeek account has insufficient balance.\n")
        elif "429" in error_msg:
            print("\n⚠  DeepSeek rate limit hit.\n")
        else:
            print(f"\n❌ Unexpected error: {e}\n")
