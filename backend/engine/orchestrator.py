"""
Report Orchestrator — full brand diagnostic pipeline.

Per README §6.2 + §9 Data Flow:
1. Firecrawl: scrape brand website → clean markdown
2. Prompt Engine: website content → Claude → positioning, SWOT, competitive, recommendations
3. SEO Scorer: SerpAPI → SERP ownership, keyword rankings, features, negative check
4. GEO Scorer: Claude + Perplexity + OpenAI → visibility, sentiment, consistency
5. Assemble final report JSON

Caching (24h TTL per README §10): not implemented yet — Sprint 2.
Cost Tracking (per README §11): records every provider call's tokens, cost, and duration.
"""

import os
import time
from datetime import datetime, timezone
from app.config import settings
from .providers.firecrawl import FirecrawlProvider, FirecrawlError
from .scorers.positioning import run_prompt_engine
from .scorers.seo import score_seo
from .scorers.geo import score_geo

# ── Provider pricing (per 1M tokens or per call) ────────
# Source: official pricing pages as of 2026-06
PRICING = {
    "deepseek":    {"input": 0.14, "output": 0.28},   # $/1M tokens
    "claude":      {"input": 3.00, "output": 15.00},  # Claude Sonnet 4.5
    "perplexity":  {"input": 1.00, "output": 1.00},   # Sonar
    "openai":      {"input": 0.15, "output": 0.60},   # GPT-4o-mini
    "firecrawl":   {"per_call": 0.0015},               # $/scrape
    "serpapi":     {"per_call": 0.0},                  # included in plan
}


def _estimate_tokens(text: str) -> int:
    """Rough token estimation: ~4 chars per token for English text."""
    return max(1, len(text) // 4)


def _record_cost(costs: list, provider: str, tokens_in: int = 0,
                 tokens_out: int = 0, duration_ms: int = 0):
    """Append a cost record for a provider call."""
    pricing = PRICING.get(provider, {})
    if "per_call" in pricing:
        cost_cents = round(pricing["per_call"] * 100)
    else:
        cost_cents = round(
            (tokens_in / 1_000_000) * pricing.get("input", 0) * 100 +
            (tokens_out / 1_000_000) * pricing.get("output", 0) * 100
        )
    costs.append({
        "provider": provider,
        "tokens_in": tokens_in if tokens_in else None,
        "tokens_out": tokens_out if tokens_out else None,
        "cost_cents": cost_cents,
        "duration_ms": duration_ms,
    })


def run_full_diagnostic(
    brand_name: str,
    website_url: str,
    industry: str = "",
    competitor: str = "",
    serpapi_key: str = None,
    firecrawl_key: str = None,
    deepseek_key: str = None,
    include_geo: bool = True,
    include_positioning: bool = True,
) -> dict:
    """
    Run all analysis engines and assemble the final brand diagnostic report.

    Returns a dict matching the `reports.payload` JSONB structure per README §7.
    Includes a `_costs` key with per-provider cost records for the report_costs table.
    """
    costs: list[dict] = []
    report = {
        "brand": brand_name,
        "website": website_url,
        "industry": industry,
        "competitor": competitor,
        "website_content": None,
        "positioning": None,
        "swot": None,
        "competitive": None,
        "recommendations": None,
        "seo": None,
        "geo": None,
        "overall_score": None,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    # ── 1. Fetch website content (Firecrawl) ─────────────
    website_text = ""
    t0 = time.monotonic()
    try:
        from .providers.mock import provider_ready, MockFirecrawl
        if provider_ready("FIRECRAWL_API_KEY"):
            firecrawl = FirecrawlProvider(api_key=settings.FIRECRAWL_API_KEY)
        else:
            firecrawl = MockFirecrawl(brand_name=brand_name, industry=industry)
        markdown, metadata = firecrawl.extract_text(website_url)
        website_text = markdown
        report["website_content"] = {
            "length_chars": len(markdown),
            "title": metadata.get("title", ""),
            "description": metadata.get("description", ""),
            "preview": markdown[:500],
        }
        _record_cost(costs, "firecrawl", duration_ms=round((time.monotonic() - t0) * 1000))
    except FirecrawlError as e:
        report["website_content"] = {"error": str(e)}

    # ── 2. Prompt Engine (positioning + SWOT + competitive) ──
    if include_positioning and website_text:
        t0 = time.monotonic()
        try:
            prompt_text = website_text[:6000]
            prompt_results = run_prompt_engine(
                brand_name=brand_name,
                website_text=website_text,
                industry=industry,
                competitor=competitor,
                seo_score=0,
                deepseek_key=deepseek_key,
            )
            report["positioning"] = prompt_results.get("positioning")
            report["swot"] = prompt_results.get("swot")
            report["competitive"] = prompt_results.get("competitive")
            report["recommendations"] = prompt_results.get("recommendations")

            # Estimate tokens: 4 LLM calls (positioning, SWOT, competitive, recommendations)
            # Each: system prompt + user prompt + website text → input, JSON response → output
            for section in ["positioning", "swot", "competitive", "recommendations"]:
                result = prompt_results.get(section, {})
                if result and "error" not in result:
                    tokens_in = _estimate_tokens(prompt_text) + 500  # prompt overhead
                    tokens_out = _estimate_tokens(str(result))
                    _record_cost(costs, "deepseek", tokens_in=tokens_in,
                                 tokens_out=tokens_out,
                                 duration_ms=round((time.monotonic() - t0) * 1000 // 4))
        except Exception as e:
            report["positioning"] = {"error": str(e)}

    # ── 3. SEO Score ─────────────────────────────────────
    t0 = time.monotonic()
    try:
        seo_result = score_seo(
            brand_name=brand_name,
            website_url=website_url,
            industry=industry,
            serpapi_key=serpapi_key,
            firecrawl_key=firecrawl_key,
        )
        report["seo"] = seo_result
        seo_score_val = seo_result.get("score", 0)
        # SEO uses ~5 SerpAPI calls + 1 Firecrawl for keyword extraction
        seo_details = seo_result.get("details", {})
        serpapi_calls = 1 + len(seo_details.get("keywords_tested", [])) + 1  # brand + keywords + negative
        for _ in range(serpapi_calls):
            _record_cost(costs, "serpapi", duration_ms=1)
        if seo_details.get("keywords_tested"):
            _record_cost(costs, "firecrawl", duration_ms=round((time.monotonic() - t0) * 1000 // 2))
    except Exception as e:
        report["seo"] = {"score": 0, "label": "Error", "error": str(e)}
        seo_score_val = 0

    # ── 4. Generate recommendations (now with SEO context) ──
    if include_positioning and website_text and report.get("recommendations") is None:
        try:
            from .scorers.positioning import generate_recommendations
            t0 = time.monotonic()
            report["recommendations"] = generate_recommendations(
                brand_name=brand_name,
                website_text=website_text,
                industry=industry,
                seo_score=seo_score_val,
                swot=report.get("swot"),
                deepseek_key=deepseek_key,
            )
            tokens_in = _estimate_tokens(website_text[:4000]) + 300
            tokens_out = _estimate_tokens(str(report["recommendations"]))
            _record_cost(costs, "deepseek", tokens_in=tokens_in, tokens_out=tokens_out,
                         duration_ms=round((time.monotonic() - t0) * 1000))
        except Exception:
            pass

    # ── 5. GEO Score ─────────────────────────────────────
    if include_geo:
        try:
            geo_result = score_geo(
                brand_name=brand_name,
                website_url=website_url,
                industry=industry,
                deepseek_key=deepseek_key,
            )
            report["geo"] = geo_result
            # GEO uses ~5 DeepSeek calls (visibility, industry, sentiment, 2x consistency)
            geo_details = geo_result.get("details", {})
            geo_engines = geo_details.get("engine_results", [])
            for eng in geo_engines:
                eng_name = eng.get("engine", "deepseek")
                for _ in range(5):  # 5 probes per engine
                    tokens_in = _estimate_tokens(
                        f"{brand_name} {industry} description"
                    ) + 300
                    tokens_out = _estimate_tokens(str(eng)) // 5
                    _record_cost(costs, eng_name, tokens_in=tokens_in,
                                 tokens_out=tokens_out, duration_ms=2000)
        except Exception as e:
            report["geo"] = {"score": 0, "label": "Error", "error": str(e)}

    # ── 5b. Meta Ads (Apify) — Radar+ tier feature ─────────
    report["meta_ads"] = None
    try:
        from .providers.mock import provider_ready, MockApify
        if provider_ready("APIFY_TOKEN"):
            from .providers.apify import ApifyProvider, ApifyError
            apify = ApifyProvider(api_key=settings.APIFY_TOKEN)
        else:
            apify = MockApify(brand_name=brand_name)
        t0 = time.monotonic()
        ads = apify.search_meta_ads(brand_name, max_results=20)
        report["meta_ads"] = {
            "total_ads_found": len(ads),
            "brand_name": brand_name,
            "ads": ads[:10],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        _record_cost(costs, "apify", duration_ms=round((time.monotonic() - t0) * 1000))
    except Exception:
        pass  # Meta Ads is optional — don't block the report if it fails

    # ── 6. Overall Score ──────────────────────────────────
    scores = []
    if report["seo"] and isinstance(report["seo"], dict) and report["seo"].get("score") is not None:
        scores.append(report["seo"]["score"])
    if report["geo"] and isinstance(report["geo"], dict) and report["geo"].get("score") is not None:
        scores.append(report["geo"]["score"])

    if scores:
        report["overall_score"] = round(sum(scores) / len(scores))

    # ── 7. Re-generate recommendations with final SEO score ──
    if include_positioning and website_text and report.get("recommendations", {}).get("error"):
        try:
            from .scorers.positioning import generate_recommendations
            report["recommendations"] = generate_recommendations(
                brand_name=brand_name,
                website_text=website_text,
                industry=industry,
                seo_score=seo_score_val,
                swot=report.get("swot"),
                deepseek_key=deepseek_key,
            )
        except Exception:
            pass

    report["_costs"] = costs
    return report
