"""
GEO Scoring Engine (Beta)
Per README §6.6 — scores brand visibility in AI responses 0–100 across 3 engines.

Engines: Claude + Perplexity + OpenAI (ChatGPT)
Fallback: DeepSeek (when primary engine keys unavailable)

Formula:
  1. Visibility  (0–40 pts) — per-engine: does the AI mention the brand?
  2. Sentiment   (0–40 pts) — per-engine: how favorably?
  3. Consistency (0–20 pts) — do engines agree on brand description?
"""

import os
from app.config import settings
from ..providers.deepseek import DeepSeekProvider, DeepSeekError

# ── Probe templates (shared across all engines) ──────────

VISIBILITY_PROBE = """What do you know about {brand_name}?

Describe what {brand_name} is, what industry it operates in, and its market position.
Return ONLY valid JSON:
{{
  "mentioned": true,
  "brand_description": "2-3 sentence factual summary",
  "industry": "the industry category",
  "confidence": "high | medium | low"
}}"""

INDUSTRY_PROBE = """What are the top brands in the {industry} industry?

Return ONLY valid JSON:
{{
  "top_brands": ["brand1", "brand2", "brand3", "brand4", "brand5"],
  "brand_mentioned": true,
  "rank_if_mentioned": 1-5
}}

IMPORTANT: {brand_name} should be in the list if it's a major player.
Set brand_mentioned to true ONLY if {brand_name} appears in your top_brands list."""

SENTIMENT_PROBE = """Analyze the brand perception of {brand_name} in the {industry} industry.

Consider: brand reputation, product/service quality, market position, innovation, customer experience.
Return ONLY valid JSON:
{{
  "sentiment": "positive | neutral | negative",
  "sentiment_score": 1-10,
  "pros": ["pro1", "pro2", "pro3"],
  "cons": ["con1", "con2"],
  "recommendation": "one sentence on whether the brand is recommended"
}}"""

CONSISTENCY_PROBE = """Describe {brand_name} in one sentence as if introducing it to someone who has never heard of it.
Return ONLY valid JSON:
{{"description": "your one-sentence description"}}"""


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def _try_get_provider(provider_name: str) -> object | None:
    """Try to initialize a provider whose key is present. Returns None if unavailable."""
    from ..providers.mock import demo_enabled, provider_ready, MockLLM
    if demo_enabled():
        # Each AI engine is a brand-seeded mock so all 3 GEO engines "respond".
        return MockLLM(engine=provider_name)
    try:
        if provider_name == "claude":
            if not provider_ready("ANTHROPIC_API_KEY"):
                return None
            from ..providers.claude import ClaudeProvider
            return ClaudeProvider(api_key=settings.ANTHROPIC_API_KEY)
        elif provider_name == "perplexity":
            if not provider_ready("PERPLEXITY_API_KEY"):
                return None
            from ..providers.perplexity import PerplexityProvider
            return PerplexityProvider(api_key=settings.PERPLEXITY_API_KEY)
        elif provider_name == "openai":
            if not provider_ready("OPENAI_API_KEY"):
                return None
            from ..providers.openai import OpenAIProvider
            return OpenAIProvider(api_key=settings.OPENAI_API_KEY)
        elif provider_name == "deepseek":
            if not provider_ready("DEEPSEEK_API_KEY"):
                return None
            return DeepSeekProvider(api_key=settings.DEEPSEEK_API_KEY)
    except Exception:
        return None
    return None


def _probe_engine(engine_name: str, provider, brand_name: str, industry: str) -> dict:
    """Run all GEO probes against one AI engine. Returns structured results."""
    result = {
        "engine": engine_name,
        "available": True,
        "visibility": {"mentioned": False, "score": 0},
        "industry_ranking": {"brand_mentioned": False, "score": 0},
        "sentiment": {"sentiment": "neutral", "score": 0},
        "consistency_descriptions": [],
        "error": None,
    }

    try:
        # Visibility probe — direct query
        v1 = provider.chat_json(VISIBILITY_PROBE.format(brand_name=brand_name))
        if v1.get("mentioned") or v1.get("brand_description"):
            confidence = v1.get("confidence", "unknown")
            conf_bonus = 3 if confidence == "high" else (2 if confidence == "medium" else 0)
            result["visibility"] = {
                "mentioned": True,
                "score": 12 + conf_bonus,  # was 7, now 12-15
                "description": v1.get("brand_description", "")[:200],
                "confidence": confidence,
            }

        # Visibility probe — industry ranking
        v2 = provider.chat_json(
            INDUSTRY_PROBE.format(brand_name=brand_name, industry=industry)
        )
        if v2.get("brand_mentioned"):
            rank = v2.get("rank_if_mentioned")
            rank_bonus = 4 if rank == 1 else (3 if rank and rank <= 3 else 1)
            result["industry_ranking"] = {
                "brand_mentioned": True,
                "score": 8 + rank_bonus,  # was 6, now 9-12
                "rank": rank,
                "top_brands": v2.get("top_brands", []),
            }

        # Sentiment probe
        s = provider.chat_json(
            SENTIMENT_PROBE.format(brand_name=brand_name, industry=industry)
        )
        sentiment_label = s.get("sentiment", "neutral").lower()
        raw_score = s.get("sentiment_score", 5)
        if sentiment_label == "positive":
            eng_sent_score = min(raw_score * 1.5, 15)  # was 1.3× / 13 max
        elif sentiment_label == "neutral":
            eng_sent_score = min(raw_score * 0.8, 8)    # was 0.7× / 7 max
        else:
            eng_sent_score = 0

        result["sentiment"] = {
            "sentiment": sentiment_label,
            "score": round(eng_sent_score, 1),
            "raw_score": raw_score,
            "pros": s.get("pros", []),
            "cons": s.get("cons", []),
            "recommendation": s.get("recommendation", ""),
        }

        # Consistency probe (2 descriptions)
        for _ in range(2):
            try:
                c = provider.chat_json(
                    CONSISTENCY_PROBE.format(brand_name=brand_name),
                    temperature=0.7,
                )
                desc = c.get("description", "")
                if desc:
                    result["consistency_descriptions"].append(desc)
            except Exception:
                pass

    except Exception as e:
        result["available"] = False
        result["error"] = str(e)

    return result


def _compute_consistency(engine_results: list[dict]) -> tuple[int, list]:
    """Compare brand descriptions across engines for consistency score."""
    all_descs = []
    for eng in engine_results:
        if eng.get("available") and eng.get("consistency_descriptions"):
            all_descs.extend(eng["consistency_descriptions"])

    if len(all_descs) < 2:
        return 10, all_descs  # default for single engine

    # Word overlap between all pairs
    overlaps = []
    for i in range(len(all_descs)):
        for j in range(i + 1, len(all_descs)):
            w1 = set(_normalize_text(all_descs[i]).split())
            w2 = set(_normalize_text(all_descs[j]).split())
            if w1 and w2:
                overlap = len(w1 & w2) / max(len(w1 | w2), 1)
                overlaps.append(overlap)

    if not overlaps:
        return 12, all_descs  # was 10

    avg_overlap = sum(overlaps) / len(overlaps)
    if avg_overlap > 0.4:     # was 0.5
        return 20, all_descs
    elif avg_overlap > 0.25:  # was 0.3
        return 14, all_descs  # was 12
    elif avg_overlap > 0.1:
        return 8, all_descs   # was 6
    return 4, all_descs       # was 2


def score_geo(brand_name: str, website_url: str = "", industry: str = "",
              deepseek_key: str = None) -> dict:
    """
    Compute GEO score (0–100) across available AI engines.

    Per README §6.6:
    - Visibility: 40 pts (split across engines)
    - Sentiment: 40 pts (split across engines)
    - Consistency: 20 pts (cross-engine comparison)

    Currently uses DeepSeek as the primary engine since Claude/Perplexity/OpenAI
    keys are not yet available. Scores are scaled to 0–100 regardless of how
    many engines run.
    """
    engine_results = []

    # ── Try each primary engine ──────────────────────────
    engine_order = ["claude", "perplexity", "openai"]
    for eng_name in engine_order:
        provider = _try_get_provider(eng_name)
        if provider:
            eng_result = _probe_engine(eng_name, provider, brand_name, industry)
            engine_results.append(eng_result)

    # ── Fallback to DeepSeek if no primary engines ────────
    if not engine_results:
        provider = _try_get_provider("deepseek")
        if provider:
            eng_result = _probe_engine("deepseek", provider, brand_name, industry)
            engine_results.append(eng_result)

    if not engine_results:
        # No real provider has a key — use brand-seeded mocks for all 3 engines
        from ..providers.mock import MockLLM
        for eng_name in engine_order:
            engine_results.append(_probe_engine(eng_name, MockLLM(engine=eng_name), brand_name, industry))

    # ── Compute scores ───────────────────────────────────
    num_engines = len([e for e in engine_results if e.get("available")])

    # Visibility: sum per-engine scores, scale to 50 max (was 40)
    vis_raw = sum(
        e.get("visibility", {}).get("score", 0) +
        e.get("industry_ranking", {}).get("score", 0)
        for e in engine_results if e.get("available")
    )
    visibility_score = min(round(vis_raw), 50)

    # Sentiment: sum per-engine sentiment scores, scale to 40 max
    sent_raw = sum(
        e.get("sentiment", {}).get("score", 0)
        for e in engine_results if e.get("available")
    )
    sentiment_score = min(round(sent_raw), 40)

    # Consistency: cross-engine overlap
    consistency_score, all_descs = _compute_consistency(engine_results)

    # ── Assemble ─────────────────────────────────────────
    total = visibility_score + sentiment_score + consistency_score
    total = min(total, 100)

    # Determine which engines were actually used
    used_engines = [e["engine"] for e in engine_results if e.get("available")]
    missing_engines = [e for e in engine_order if e not in used_engines]

    # Calibrated label thresholds
    if total >= 85:
        label = "Excellent"
    elif total >= 70:
        label = "Strong"
    elif total >= 50:
        label = "Average"
    elif total >= 30:
        label = "Weak"
    else:
        label = "Limited"

    return {
        "score": total,
        "label": label,
        "breakdown": {
            "visibility": visibility_score,
            "sentiment": sentiment_score,
            "consistency": consistency_score,
        },
        "details": {
            "engines_used": used_engines,
            "engines_unavailable": missing_engines,
            "engine_results": engine_results,
            "consistency_descriptions": all_descs,
        },
    }
