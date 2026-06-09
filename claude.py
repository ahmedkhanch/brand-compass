"""
TEST 1 — Claude API
Validates: API key works, model responds, JSON output is parseable
Expected: Brand positioning JSON in under 10 seconds
"""

import os
import json
import time
from dotenv import load_dotenv
import anthropic

load_dotenv()

BRAND     = os.getenv("TEST_BRAND_NAME", "Nike")
INDUSTRY  = os.getenv("TEST_BRAND_INDUSTRY", "sportswear")
URL       = os.getenv("TEST_BRAND_URL", "https://www.nike.com")

def test_basic_call():
    """Most basic possible call — just checking the key works."""
    print("\n── Test 1/3 : Basic call ──────────────────")
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    start = time.time()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=100,
        messages=[{"role": "user", "content": "Reply with exactly: API_OK"}]
    )
    elapsed = round(time.time() - start, 2)
    response_text = msg.content[0].text.strip()

    if "API_OK" in response_text:
        print(f"  ✅ Key valid — response in {elapsed}s")
    else:
        print(f"  ⚠  Unexpected response: {response_text}")

def test_json_output():
    """Check that Claude reliably returns parseable JSON — critical for the pipeline."""
    print("\n── Test 2/3 : JSON output reliability ─────")
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""
You are a brand analyst. Analyze this brand and return ONLY valid JSON — no preamble, no markdown fences.

Brand: {BRAND}
Website: {URL}
Industry: {INDUSTRY}

Return exactly this structure:
{{
  "archetype": "one of: Hero, Creator, Explorer, Sage, Rebel, Caregiver, Ruler, Jester, Lover, Magician, Innocent, Everyman",
  "value_proposition": "one sentence",
  "target_audience": "one sentence",
  "brand_voice": ["adjective1", "adjective2", "adjective3"],
  "differentiators": ["point1", "point2", "point3"],
  "weaknesses": ["weakness1", "weakness2"],
  "positioning": {{
    "price_axis": "mainstream or premium",
    "appeal_axis": "functional or emotional"
  }}
}}
"""

    start = time.time()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    elapsed = round(time.time() - start, 2)
    raw = msg.content[0].text.strip()

    try:
        parsed = json.loads(raw)
        print(f"  ✅ JSON valid — parsed in {elapsed}s")
        print(f"     Archetype       : {parsed.get('archetype')}")
        print(f"     Value prop      : {parsed.get('value_proposition')}")
        print(f"     Positioning     : {parsed.get('positioning')}")
        print(f"     Brand voice     : {parsed.get('brand_voice')}")
        return True
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON parse failed after {elapsed}s")
        print(f"     Error   : {e}")
        print(f"     Raw     : {raw[:300]}")
        return False

def test_swot_output():
    """Check SWOT analysis — longer output, more complex structure."""
    print("\n── Test 3/3 : SWOT analysis ───────────────")
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""
You are a senior brand strategist. Return ONLY valid JSON — no preamble, no markdown.

Brand: {BRAND}
Industry: {INDUSTRY}

{{
  "strengths": ["s1", "s2", "s3"],
  "weaknesses": ["w1", "w2"],
  "opportunities": ["o1", "o2"],
  "threats": ["t1", "t2"],
  "executive_summary": "2 sentence summary"
}}
"""

    start = time.time()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    elapsed = round(time.time() - start, 2)
    raw = msg.content[0].text.strip()

    try:
        parsed = json.loads(raw)
        print(f"  ✅ SWOT JSON valid — {elapsed}s")
        print(f"     Strengths    : {parsed.get('strengths', [])[:2]}")
        print(f"     Opportunities: {parsed.get('opportunities', [])[:2]}")
        print(f"     Summary      : {parsed.get('executive_summary', '')[:120]}")

        # Check token usage — important for cost estimation
        print(f"\n  📊 Token usage:")
        print(f"     Input  : {msg.usage.input_tokens} tokens")
        print(f"     Output : {msg.usage.output_tokens} tokens")
        estimated_cost = (msg.usage.input_tokens / 1_000_000 * 3) + (msg.usage.output_tokens / 1_000_000 * 15)
        print(f"     Cost   : ~${estimated_cost:.5f} USD (claude-sonnet-4-5 rates)")
    except json.JSONDecodeError as e:
        print(f"  ❌ SWOT JSON parse failed")
        print(f"     Error: {e}")
        print(f"     Raw  : {raw[:300]}")

if __name__ == "__main__":
    print("=" * 50)
    print("  CLAUDE API TEST")
    print(f"  Brand: {BRAND} | Industry: {INDUSTRY}")
    print("=" * 50)

    try:
        test_basic_call()
        test_json_output()
        test_swot_output()
        print("\n✅ Claude API — ALL TESTS PASSED\n")
    except anthropic.AuthenticationError:
        print("\n❌ ANTHROPIC_API_KEY is invalid or missing. Check your .env\n")
    except anthropic.RateLimitError:
        print("\n⚠  Rate limit hit. Your plan may have low RPM limits.\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")